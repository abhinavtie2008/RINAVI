import pytest
from httpx import ASGITransport, AsyncClient, Cookies
from sqlalchemy import func, select

from app.core.db import async_session_factory
from app.main import app
from app.modules.audit.models import AuditEvent
from app.modules.consent.models import ConsentRecord
from app.modules.identity.models import Session, User


def make_client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies=Cookies(),
    )


async def count(db, model) -> int:
    result = await db.execute(select(func.count()).select_from(model))
    return result.scalar_one()


async def test_delete_account_wipes_owned_data_and_keeps_audit() -> None:
    async with make_client() as client:
        await client.post(
            "/api/v1/auth/dev-signin", json={"email": "citizen@example.com"}
        )
        await client.post(
            "/api/v1/consent/grants", json={"purpose": "documents.processing"}
        )

        response = await client.delete("/api/v1/auth/account")
        assert response.status_code == 204

        set_cookies = response.headers.get_list("set-cookie")
        clearing = next(h for h in set_cookies if "rinavi_session" in h)
        assert "max-age=0" in clearing.lower()

        me = await client.get("/api/v1/auth/me")
        assert me.status_code == 401

    async with async_session_factory() as db:
        assert await count(db, User) == 0
        assert await count(db, Session) == 0
        assert await count(db, ConsentRecord) == 0

        events = (await db.execute(select(AuditEvent))).scalars().all()
        assert len(events) == 1
        assert events[0].action == "account.deleted"
        assert events[0].resource_type == "user"
        assert events[0].actor_user_id is None
        assert "citizen@example.com" not in events[0].details.values()


async def test_deleting_one_user_leaves_others_untouched() -> None:
    async with make_client() as client_a:
        await client_a.post(
            "/api/v1/auth/dev-signin", json={"email": "alice@example.com"}
        )
        async with make_client() as client_b:
            await client_b.post(
                "/api/v1/auth/dev-signin", json={"email": "bob@example.com"}
            )
            await client_b.post(
                "/api/v1/consent/grants", json={"purpose": "documents.processing"}
            )

            response = await client_a.delete("/api/v1/auth/account")
            assert response.status_code == 204

            me = await client_b.get("/api/v1/auth/me")
            assert me.status_code == 200
            assert me.json()["email"] == "bob@example.com"

    async with async_session_factory() as db:
        users = (await db.execute(select(User))).scalars().all()
        assert [u.email for u in users] == ["bob@example.com"]
        consents = (await db.execute(select(ConsentRecord))).scalars().all()
        assert len(consents) == 1
        assert (await count(db, Session)) == 1


async def test_delete_account_requires_auth() -> None:
    async with make_client() as client:
        response = await client.delete("/api/v1/auth/account")
        assert response.status_code == 401


async def test_export_returns_only_own_data() -> None:
    async with make_client() as client_a:
        await client_a.post(
            "/api/v1/auth/dev-signin", json={"email": "alice@example.com"}
        )
        await client_a.post(
            "/api/v1/consent/grants", json={"purpose": "documents.processing"}
        )
        async with make_client() as client_b:
            await client_b.post(
                "/api/v1/auth/dev-signin", json={"email": "bob@example.com"}
            )
            await client_b.post(
                "/api/v1/consent/grants", json={"purpose": "profile.sharing"}
            )

        response = await client_a.get("/api/v1/auth/export")
        assert response.status_code == 200
        body = response.json()
        assert body["user"]["email"] == "alice@example.com"
        assert len(body["consent_records"]) == 1
        assert body["consent_records"][0]["purpose"] == "documents.processing"


async def test_export_requires_auth() -> None:
    async with make_client() as client:
        response = await client.get("/api/v1/auth/export")
        assert response.status_code == 401


class FailingStorage:
    def purge_user(self, _user_id: object) -> None:
        raise OSError("storage unavailable")


async def test_delete_account_keeps_account_when_storage_purge_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.modules.identity.routes as identity_routes

    monkeypatch.setattr(identity_routes, "get_storage", lambda: FailingStorage())

    async with make_client() as client:
        await client.post(
            "/api/v1/auth/dev-signin", json={"email": "citizen@example.com"}
        )
        response = await client.delete("/api/v1/auth/account")
        assert response.status_code == 503
        me = await client.get("/api/v1/auth/me")
        assert me.status_code == 200

    async with async_session_factory() as db:
        assert await count(db, User) == 1
