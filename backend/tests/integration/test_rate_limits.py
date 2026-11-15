import hashlib
import logging

import pytest
from httpx import ASGITransport, AsyncClient, Cookies, Response

from app.core.config import get_settings
from app.main import app

API = "/api/v1"


def global_budget() -> int:
    return int(get_settings().rate_limit_default.split("/", 1)[0])

INCOME_TEXT = (
    "Applicant Name: Asha Devi\n"
    "Father's Name: Rajesh Devi\n"
    "Date of Birth: 12/03/1994\n"
    "Gender: Female\n"
    "Address: 14, Nehru Colony, Example Nagar\n"
    "Annual Income: Rs. 1,20,000\n"
)


def make_client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", cookies=Cookies()
    )


async def sign_in(client: AsyncClient, email: str = "citizen@example.com") -> str:
    response = await client.post(f"{API}/auth/dev-signin", json={"email": email})
    assert response.status_code == 200
    return response.json()["id"]


async def allow(client: AsyncClient, purpose: str) -> None:
    response = await client.post(f"{API}/consent/grants", json={"purpose": purpose})
    assert response.status_code == 201


async def upload_income_document(client: AsyncClient) -> str:
    response = await client.post(
        f"{API}/vault/documents",
        files={"file": ("income.txt", INCOME_TEXT.encode(), "text/plain")},
    )
    assert response.status_code == 201
    return response.json()["id"]


def assert_rate_limited(response: Response) -> None:
    assert response.status_code == 429
    assert response.json()["detail"]
    assert "retry-after" in response.headers


async def test_dev_signin_is_rate_limited_per_ip() -> None:
    async with make_client() as client:
        for _ in range(5):
            response = await client.post(
                f"{API}/auth/dev-signin", json={"email": "citizen@example.com"}
            )
            assert response.status_code == 200
        response = await client.post(
            f"{API}/auth/dev-signin", json={"email": "citizen@example.com"}
        )
        assert_rate_limited(response)


async def test_passkey_login_begin_is_rate_limited_per_ip() -> None:
    async with make_client() as client:
        for _ in range(10):
            assert (await client.post(f"{API}/auth/passkey/login/begin")).status_code == 200
        response = await client.post(f"{API}/auth/passkey/login/begin")
        assert_rate_limited(response)


async def test_document_content_is_rate_limited_per_session() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "documents.processing")
        document_id = await upload_income_document(client)
        url = f"{API}/vault/documents/{document_id}/content"
        for _ in range(100):
            assert (await client.get(url)).status_code == 200
        response = await client.get(url)
        assert_rate_limited(response)

    # A different session on the same IP keeps its own budget: the request
    # reaches authorization (404) instead of being throttled.
    async with make_client() as other:
        await sign_in(other, email="other@example.com")
        await allow(other, "documents.processing")
        response = await other.get(f"{API}/vault/documents/{document_id}/content")
        assert response.status_code == 404


async def test_account_export_is_rate_limited_per_session() -> None:
    async with make_client() as client:
        await sign_in(client)
        for _ in range(20):
            assert (await client.get(f"{API}/auth/export")).status_code == 200
        response = await client.get(f"{API}/auth/export")
        assert_rate_limited(response)


async def test_global_default_limit_applies_per_session() -> None:
    limit = global_budget()
    async with make_client() as client:
        await sign_in(client)
        # The sign-in itself is keyed by IP (no session yet), so the session's
        # own budget starts empty.
        for _ in range(limit):
            assert (await client.get(f"{API}/auth/me")).status_code == 200
        assert_rate_limited(await client.get(f"{API}/auth/me"))


async def test_global_budget_is_per_session_not_per_ip() -> None:
    # Two citizens behind one NAT share an address but not a session: one
    # exhausting their budget must not throttle the other.
    limit = global_budget()
    async with make_client() as first, make_client() as second:
        await sign_in(first, email="first@example.com")
        await sign_in(second, email="second@example.com")

        for _ in range(limit):
            assert (await first.get(f"{API}/auth/me")).status_code == 200
        assert_rate_limited(await first.get(f"{API}/auth/me"))

        assert (await second.get(f"{API}/auth/me")).status_code == 200


async def test_health_probes_are_not_rate_limited() -> None:
    async with make_client() as client:
        for _ in range(250):
            assert (await client.get(f"{API}/health")).status_code == 200
        # Health did not consume the global budget: an unauthenticated call
        # still reaches the endpoint (401) instead of being throttled.
        assert (await client.get(f"{API}/auth/me")).status_code == 401


async def test_preflights_do_not_consume_the_global_budget() -> None:
    async with make_client() as client:
        await sign_in(client)
        for _ in range(250):
            response = await client.options(
                f"{API}/auth/me",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )
            assert response.status_code == 200
        assert (await client.get(f"{API}/auth/me")).status_code == 200


async def test_rate_limit_response_includes_cors_headers() -> None:
    async with make_client() as client:
        for _ in range(5):
            response = await client.post(
                f"{API}/auth/dev-signin",
                json={"email": "citizen@example.com"},
                headers={"Origin": "http://localhost:3000"},
            )
            assert response.status_code == 200

        limited = await client.post(
            f"{API}/auth/dev-signin",
            json={"email": "citizen@example.com"},
            headers={"Origin": "http://localhost:3000"},
        )

        assert_rate_limited(limited)
        assert (
            limited.headers["access-control-allow-origin"]
            == "http://localhost:3000"
        )
        assert limited.headers["access-control-allow-credentials"] == "true"


async def test_session_token_is_not_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async with make_client() as client:
        await sign_in(client)
        token = client.cookies.get("rinavi_session")
        assert token is not None
        await allow(client, "documents.processing")
        document_id = await upload_income_document(client)
        url = f"{API}/vault/documents/{document_id}/content"
        for _ in range(100):
            assert (await client.get(url)).status_code == 200

        caplog.clear()
        caplog.set_level(logging.WARNING)
        assert_rate_limited(await client.get(url))

    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    assert token not in caplog.text
    assert f"session:{digest}" in caplog.text
