import base64
import json

from httpx import ASGITransport, AsyncClient, Cookies

from app.main import app


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def make_client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies=Cookies(),
    )


async def sign_in(client: AsyncClient, email: str) -> None:
    response = await client.post("/api/v1/auth/dev-signin", json={"email": email})
    assert response.status_code == 200


async def test_register_begin_requires_auth() -> None:
    async with make_client() as client:
        response = await client.post("/api/v1/auth/passkey/register/begin")
        assert response.status_code == 401


async def test_register_begin_returns_webauthn_options() -> None:
    async with make_client() as client:
        await sign_in(client, "citizen@example.com")
        response = await client.post("/api/v1/auth/passkey/register/begin")
        assert response.status_code == 200
        body = response.json()
        assert body["challenge_id"]
        options = body["options"]
        assert options["rp"]["id"] == "localhost"
        assert options["rp"]["name"] == "RINAVI"
        assert options["user"]["name"] == "citizen@example.com"
        assert "challenge" in options


async def test_register_finish_with_unknown_challenge_fails_closed() -> None:
    async with make_client() as client:
        await sign_in(client, "citizen@example.com")
        response = await client.post(
            "/api/v1/auth/passkey/register/finish",
            json={"challenge_id": "never-issued", "credential": "{}"},
        )
        assert response.status_code == 400


async def test_register_finish_with_garbage_credential_fails_closed() -> None:
    async with make_client() as client:
        await sign_in(client, "citizen@example.com")
        begin = await client.post("/api/v1/auth/passkey/register/begin")
        challenge_id = begin.json()["challenge_id"]
        response = await client.post(
            "/api/v1/auth/passkey/register/finish",
            json={"challenge_id": challenge_id, "credential": "not json"},
        )
        assert response.status_code == 400


async def test_login_begin_returns_webauthn_options() -> None:
    async with make_client() as client:
        response = await client.post("/api/v1/auth/passkey/login/begin")
        assert response.status_code == 200
        body = response.json()
        assert body["challenge_id"]
        options = body["options"]
        assert options["rpId"] == "localhost"
        assert "challenge" in options


async def test_login_finish_with_malformed_credential_returns_400() -> None:
    async with make_client() as client:
        begin = await client.post("/api/v1/auth/passkey/login/begin")
        challenge_id = begin.json()["challenge_id"]
        response = await client.post(
            "/api/v1/auth/passkey/login/finish",
            json={
                "challenge_id": challenge_id,
                "credential": json.dumps(
                    {
                        "id": "unknown-credential",
                        "rawId": "unknown-credential",
                        "type": "public-key",
                        "response": {},
                    }
                ),
            },
        )
        assert response.status_code == 400


async def test_login_finish_with_unknown_valid_credential_returns_401() -> None:
    async with make_client() as client:
        begin = await client.post("/api/v1/auth/passkey/login/begin")
        challenge_id = begin.json()["challenge_id"]
        raw_id = b64url(b"unknown-credential")
        response = await client.post(
            "/api/v1/auth/passkey/login/finish",
            json={
                "challenge_id": challenge_id,
                "credential": json.dumps(
                    {
                        "id": raw_id,
                        "rawId": raw_id,
                        "type": "public-key",
                        "response": {
                            "clientDataJSON": b64url(b'{"type":"webauthn.get"}'),
                            "authenticatorData": b64url(b"\x00" * 37),
                            "signature": b64url(b"\x00" * 64),
                        },
                    }
                ),
            },
        )
        assert response.status_code == 401
