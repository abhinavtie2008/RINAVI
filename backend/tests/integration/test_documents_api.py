from httpx import ASGITransport, AsyncClient, Cookies
from sqlalchemy import select

from app.core.db import async_session_factory
from app.main import app
from app.modules.audit.models import AuditEvent

API = "/api/v1"


def make_client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies=Cookies(),
    )


async def sign_in(client: AsyncClient, email: str = "citizen@example.com") -> None:
    response = await client.post(f"{API}/auth/dev-signin", json={"email": email})
    assert response.status_code == 200


async def allow_documents(client: AsyncClient) -> None:
    response = await client.post(
        f"{API}/consent/grants", json={"purpose": "documents.processing"}
    )
    assert response.status_code == 201


async def upload(
    client: AsyncClient,
    *,
    name: str = "certificate.txt",
    content: bytes = b"Name: Asha Devi\n",
    content_type: str = "text/plain",
):
    return await client.post(
        f"{API}/vault/documents",
        files={"file": (name, content, content_type)},
    )


async def test_upload_requires_session() -> None:
    async with make_client() as client:
        response = await upload(client)
        assert response.status_code == 401


async def test_upload_requires_document_consent() -> None:
    async with make_client() as client:
        await sign_in(client)
        response = await upload(client)
        assert response.status_code == 403


async def test_upload_stores_document_and_returns_metadata() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow_documents(client)
        content = b"Name: Asha Devi\n"

        response = await upload(client, content=content)

        assert response.status_code == 201
        body = response.json()
        assert body["original_filename"] == "certificate.txt"
        assert body["content_type"] == "text/plain"
        assert body["size_bytes"] == len(content)
        # Task 4 flips this to "processed" once the pipeline is wired in.
        assert body["status"] == "quarantined"

        fetched = await client.get(f"{API}/vault/documents/{body['id']}/content")
        assert fetched.status_code == 200
        assert fetched.headers["content-type"].startswith("text/plain")
        assert fetched.content == content


async def test_unsupported_content_is_rejected() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow_documents(client)

        response = await upload(
            client,
            name="archive.zip",
            content=b"PK\x03\x04not-a-document",
            content_type="application/zip",
        )

        assert response.status_code == 415


async def test_oversized_upload_is_rejected() -> None:
    from app.modules.vault.validation import MAX_UPLOAD_BYTES

    async with make_client() as client:
        await sign_in(client)
        await allow_documents(client)

        response = await upload(
            client,
            content=b"%PDF-1.7\n" + b"0" * MAX_UPLOAD_BYTES,
            content_type="application/pdf",
        )

        assert response.status_code == 413


async def test_list_and_get_are_scoped_to_the_owner() -> None:
    async with make_client() as alice:
        await sign_in(alice, "alice@example.com")
        await allow_documents(alice)
        created = await upload(alice)
        document_id = created.json()["id"]

        listed = await alice.get(f"{API}/vault/documents")
        assert listed.status_code == 200
        assert [d["id"] for d in listed.json()] == [document_id]

        async with make_client() as bob:
            await sign_in(bob, "bob@example.com")
            await allow_documents(bob)

            assert (await bob.get(f"{API}/vault/documents")).json() == []
            assert (
                await bob.get(f"{API}/vault/documents/{document_id}")
            ).status_code == 404
            assert (
                await bob.get(f"{API}/vault/documents/{document_id}/content")
            ).status_code == 404


async def test_upload_emits_redacted_audit_event() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow_documents(client)
        await upload(client)

    async with async_session_factory() as db:
        events = (await db.execute(select(AuditEvent))).scalars().all()
        uploaded = [e for e in events if e.action == "document.uploaded"]
        assert len(uploaded) == 1
        assert uploaded[0].resource_type == "document"
        assert "filename" not in uploaded[0].details
        assert "Asha Devi" not in str(uploaded[0].details.values())
