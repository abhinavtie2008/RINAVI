from httpx import ASGITransport, AsyncClient, Cookies
from starlette.types import Message

from app.main import app

API = "/api/v1"

MIB = 1024 * 1024


def make_client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies=Cookies(),
    )


async def sign_in(client: AsyncClient) -> None:
    response = await client.post(f"{API}/auth/dev-signin", json={"email": "citizen@example.com"})
    assert response.status_code == 200


async def allow(client: AsyncClient, purpose: str) -> None:
    response = await client.post(f"{API}/consent/grants", json={"purpose": purpose})
    assert response.status_code == 201


async def upload(client: AsyncClient, content: bytes, filename: str):
    return await client.post(
        f"{API}/vault/documents",
        files={"file": (filename, content, "image/png")},
    )


async def test_oversized_json_body_is_rejected_with_413() -> None:
    # No session is involved: the body limit sits outside authentication, and
    # the 413 must carry the CORS and security headers that wrap the limiter.
    async with make_client() as client:
        response = await client.post(
            f"{API}/consent/grants",
            json={"purpose": "x" * (MIB + 1)},
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 413
        assert response.json()["detail"]
        assert response.headers["x-content-type-options"] == "nosniff"
        assert (
            response.headers["access-control-allow-origin"]
            == "http://localhost:3000"
        )
        # The body limit runs outside the rate limiter, so a rejected body
        # never consumes the request budget and carries no limit headers.
        assert "x-ratelimit-limit" not in response.headers


async def test_chunked_oversized_json_body_is_rejected() -> None:
    body = b'{"purpose": "' + b"x" * (MIB + 1) + b'"}'
    chunks = [body[i : i + 4096] for i in range(0, len(body), 4096)]
    index = 0

    async def receive() -> Message:
        nonlocal index
        if index < len(chunks):
            message: Message = {
                "type": "http.request",
                "body": chunks[index],
                "more_body": index < len(chunks) - 1,
            }
            index += 1
            return message
        return {"type": "http.disconnect"}

    responses: list[Message] = []

    async def send(message: Message) -> None:
        responses.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": f"{API}/consent/grants",
        "raw_path": f"{API}/consent/grants".encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [
            (b"host", b"test"),
            (b"content-type", b"application/json"),
        ],
        "client": ("127.0.0.1", 50000),
        "server": ("test", 80),
    }
    await app(scope, receive, send)
    start = next(m for m in responses if m["type"] == "http.response.start")
    assert start["status"] == 413


async def test_oversized_non_json_body_is_rejected_with_413() -> None:
    # A body that is not JSON falls under the larger ceiling, which exists to
    # leave room for the 10 MB document upload; 12 MB must still be rejected.
    async with make_client() as client:
        response = await client.post(
            f"{API}/consent/grants",
            content=b"x" * (12 * MIB),
            headers={"content-type": "text/plain"},
        )
        assert response.status_code == 413
        assert response.json()["detail"]


async def test_max_size_upload_is_accepted() -> None:
    # Exactly 10 MB of file content: the application's own upload cap accepts
    # it, and the body limit's 11 MB ceiling must not reject it first.
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "documents.processing")
        png = b"\x89PNG\r\n\x1a\n" + b"\x00" * (10 * MIB - 8)
        response = await upload(client, png, "scan.png")
        assert response.status_code == 201


async def test_upload_one_byte_over_the_application_cap_is_rejected() -> None:
    # The upload endpoint reads one byte past its own 10 MB cap and answers
    # 413; the body limit must not change that outcome.
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "documents.processing")
        png = b"\x89PNG\r\n\x1a\n" + b"\x00" * (10 * MIB + 1 - 8)
        response = await upload(client, png, "scan.png")
        assert response.status_code == 413
