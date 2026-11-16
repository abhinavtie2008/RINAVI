from httpx import ASGITransport, AsyncClient, Cookies

from app.main import app


def make_client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies=Cookies(),
    )


async def test_dev_signin_creates_session_and_me() -> None:
    async with make_client() as client:
        response = await client.post(
            "/api/v1/auth/dev-signin", json={"email": "citizen@example.com"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["email"] == "citizen@example.com"
        assert body["display_name"] == "citizen"
        assert "id" in body

        me = await client.get("/api/v1/auth/me")
        assert me.status_code == 200
        assert me.json()["email"] == "citizen@example.com"


async def test_signin_is_idempotent() -> None:
    async with make_client() as client:
        first = await client.post(
            "/api/v1/auth/dev-signin", json={"email": "citizen@example.com"}
        )
        second = await client.post(
            "/api/v1/auth/dev-signin", json={"email": "citizen@example.com"}
        )
        assert first.json()["id"] == second.json()["id"]


async def test_me_without_session_returns_401() -> None:
    async with make_client() as client:
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401


async def test_me_with_garbage_cookie_returns_401() -> None:
    async with make_client() as client:
        client.cookies.set("rinavi_session", "not-a-real-token", domain="test")
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401


async def test_logout_revokes_session() -> None:
    async with make_client() as client:
        await client.post(
            "/api/v1/auth/dev-signin", json={"email": "citizen@example.com"}
        )
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 204

        me = await client.get("/api/v1/auth/me")
        assert me.status_code == 401


async def test_session_cookie_is_httponly_and_samesite_lax() -> None:
    async with make_client() as client:
        response = await client.post(
            "/api/v1/auth/dev-signin", json={"email": "citizen@example.com"}
        )
        set_cookies = response.headers.get_list("set-cookie")
        session_header = next(
            header for header in set_cookies if "rinavi_session" in header
        )
        assert "httponly" in session_header.lower()
        assert "samesite=lax" in session_header.lower()


async def test_dev_signin_disabled_returns_404(monkeypatch) -> None:
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "dev_signin_enabled", False)
    async with make_client() as client:
        response = await client.post(
            "/api/v1/auth/dev-signin", json={"email": "citizen@example.com"}
        )
        assert response.status_code == 404


async def test_dev_signin_and_logout_emit_audit_events() -> None:
    from sqlalchemy import select

    from app.core.db import async_session_factory
    from app.modules.audit.models import AuditEvent

    async with make_client() as client:
        signin = await client.post(
            "/api/v1/auth/dev-signin", json={"email": "citizen@example.com"}
        )
        user_id = signin.json()["id"]
        await client.post("/api/v1/auth/logout")

    async with async_session_factory() as db:
        events = (await db.execute(select(AuditEvent))).scalars().all()
        signed_in = [e for e in events if e.action == "identity.signed_in"]
        signed_out = [e for e in events if e.action == "identity.signed_out"]

        assert len(signed_in) == 1
        assert str(signed_in[0].actor_user_id) == user_id
        assert signed_in[0].resource_type == "user"
        assert signed_in[0].resource_id == user_id
        assert signed_in[0].details == {"method": "dev"}

        assert len(signed_out) == 1
        assert str(signed_out[0].actor_user_id) == user_id
        assert signed_out[0].resource_type == "user"
        assert signed_out[0].resource_id == user_id
