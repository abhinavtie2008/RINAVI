import pytest
from fastapi import HTTPException

from app.api.deps import require_active_consent
from app.core.db import async_session_factory
from app.modules.consent import service as consent_service
from app.modules.identity import service as identity_service


async def test_guard_blocks_without_consent() -> None:
    async with async_session_factory() as db:
        user = await identity_service.get_or_create_user(db, "citizen@example.com")
        await db.commit()
        with pytest.raises(HTTPException) as exc_info:
            await require_active_consent("documents.processing", user, db)
        assert exc_info.value.status_code == 403


async def test_guard_passes_with_active_consent() -> None:
    async with async_session_factory() as db:
        user = await identity_service.get_or_create_user(db, "citizen@example.com")
        await consent_service.grant_consent(db, user, "documents.processing")
        await db.commit()
        await require_active_consent("documents.processing", user, db)


async def test_guard_blocks_after_withdrawal() -> None:
    async with async_session_factory() as db:
        user = await identity_service.get_or_create_user(db, "citizen@example.com")
        await consent_service.grant_consent(db, user, "documents.processing")
        await consent_service.withdraw_consent(db, user, "documents.processing")
        await db.commit()
        with pytest.raises(HTTPException) as exc_info:
            await require_active_consent("documents.processing", user, db)
        assert exc_info.value.status_code == 403


async def test_consent_required_wires_as_route_dependency() -> None:
    from typing import Any

    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient, Cookies

    from app.api.deps import ConsentRequired, CurrentUser, DbSession

    probe = FastAPI()

    @probe.get("/probe")
    async def probe_route(
        user: CurrentUser,
        db: DbSession,
        _guard: Any = ConsentRequired("documents.processing"),  # noqa: B008
    ) -> dict:
        return {"email": user.email}

    async with async_session_factory() as db:
        user = await identity_service.get_or_create_user(db, "citizen@example.com")
        token = await identity_service.create_session(db, user)
        await db.commit()

    transport = ASGITransport(app=probe)
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=Cookies()
    ) as client:
        client.cookies.set("rinavi_session", token, domain="test.local")
        blocked = await client.get("/probe")
        assert blocked.status_code == 403
        async with async_session_factory() as db:
            user = await identity_service.get_or_create_user(db, "citizen@example.com")
            await consent_service.grant_consent(db, user, "documents.processing")
            await db.commit()
        allowed = await client.get("/probe")
        assert allowed.status_code == 200
        assert allowed.json() == {"email": "citizen@example.com"}
