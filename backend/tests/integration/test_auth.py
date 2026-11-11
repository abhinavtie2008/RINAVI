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


async def test_dev_signin_disabled_returns_404(monkeypatch) -> None:
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "dev_signin_enabled", False)
    async with make_client() as client:
        response = await client.post(
            "/api/v1/auth/dev-signin", json={"email": "citizen@example.com"}
        )
        assert response.status_code == 404
