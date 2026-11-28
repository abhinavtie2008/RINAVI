import re
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.api.deps import require_active_consent
from app.core.config import get_settings
from app.core.db import async_session_factory
from app.modules.consent import service as consent_service
from app.modules.consent.models import ConsentRecord
from app.modules.consent.purposes import CONSENT_PURPOSES
from app.modules.identity import service as identity_service

DATA_MAP = Path(__file__).resolve().parents[3] / "docs" / "compliance" / "data-map.md"


def documented_purposes() -> tuple[str, ...]:
    """The purpose column of the §4 table, in document order."""
    text = DATA_MAP.read_text(encoding="utf-8")
    start = text.index("## 4.")
    section = text[start : text.index("\n## ", start)]
    purposes: list[str] = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        first_cell = line.split("|")[1]
        match = re.search(r"`([^`]+)`", first_cell)
        if match:
            purposes.append(match.group(1))
    return tuple(purposes)


def test_code_and_data_map_agree_on_the_purposes() -> None:
    # docs/compliance/data-map.md §4 is the normative list; CONSENT_PURPOSES is
    # what the schema and the route guards enforce. A purpose added, removed or
    # renamed on either side must fail here rather than quietly widen consent.
    assert documented_purposes() == CONSENT_PURPOSES
    assert len(CONSENT_PURPOSES) == 4


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


async def test_guard_blocks_a_grant_made_under_an_older_policy() -> None:
    # The version is recorded with the grant, so it must also be enforced:
    # bumping the notice has to ask the citizen again rather than reuse the
    # permission they gave for the previous text.
    async with async_session_factory() as db:
        user = await identity_service.get_or_create_user(db, "citizen@example.com")
        db.add(
            ConsentRecord(
                user_id=user.id,
                purpose="documents.processing",
                policy_version="0.9",
            )
        )
        await db.commit()

        with pytest.raises(HTTPException) as exc_info:
            await require_active_consent("documents.processing", user, db)
        assert exc_info.value.status_code == 403


async def test_guard_survives_duplicate_active_grants() -> None:
    async with async_session_factory() as db:
        user = await identity_service.get_or_create_user(db, "citizen@example.com")
        await consent_service.grant_consent(db, user, "documents.processing")
        # Simulate a grant race: a second active record for the same purpose.
        db.add(
            ConsentRecord(
                user_id=user.id,
                purpose="documents.processing",
                policy_version=get_settings().consent_policy_version,
            )
        )
        await db.commit()
        await require_active_consent("documents.processing", user, db)


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
