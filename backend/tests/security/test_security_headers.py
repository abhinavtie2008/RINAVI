import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

import app.main as main_module
from app.core.config import Settings
from app.main import app

API = "/api/v1"


def make_client(target=app) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=target), base_url="http://test")


def _production_app(monkeypatch: pytest.MonkeyPatch):
    production = Settings(
        environment="production",
        dev_signin_enabled=False,
        cookie_secure=True,
        webauthn_origin="https://rinavi.example",
        storage_encryption_key=SecretStr(
            "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY"
        ),
    )
    monkeypatch.setattr(main_module, "get_settings", lambda: production)
    return main_module.create_app()


async def test_responses_carry_security_headers() -> None:
    async with make_client() as client:
        response = await client.get(f"{API}/health")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "geolocation=()" in response.headers["permissions-policy"]
    # Every API response can hold personal data; none may be reused from a
    # shared cache or the browser's back/forward store.
    assert response.headers["cache-control"] == "no-store"


async def test_hsts_is_not_sent_outside_production() -> None:
    # HSTS is meaningless (and misleading) when the app is served over http in
    # development and tests.
    async with make_client() as client:
        response = await client.get(f"{API}/health")
    assert "strict-transport-security" not in response.headers


async def test_api_docs_are_available_outside_production() -> None:
    async with make_client() as client:
        assert (await client.get("/docs")).status_code == 200
        assert (await client.get("/openapi.json")).status_code == 200


def test_api_docs_are_disabled_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    production_app = _production_app(monkeypatch)
    assert production_app.openapi_url is None
    assert "/docs" not in {
        getattr(route, "path", None) for route in production_app.routes
    }


async def test_hsts_is_sent_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    production_app = _production_app(monkeypatch)
    async with make_client(production_app) as client:
        response = await client.get(f"{API}/health")
    assert response.headers["strict-transport-security"].startswith(
        "max-age=31536000"
    )
