import uuid

import pytest
from httpx import ASGITransport, AsyncClient, Cookies
from sqlalchemy import select

from app.core.db import async_session_factory
from app.main import app
from app.modules.audit.models import AuditEvent
from app.modules.vault.storage import get_storage

API = "/api/v1"

INCOME_TEXT = (
    "Applicant Name: Asha Devi\n"
    "Father's Name: Rajesh Devi\n"
    "Date of Birth: 12/03/1994\n"
    "Gender: Female\n"
    "Address: 14, Nehru Colony, Example Nagar\n"
    "Annual Income: Rs. 1,20,000\n"
    "Aadhaar: 1234 5678 9012\n"
)


def make_client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies=Cookies(),
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
    assert response.json()["status"] == "processed"
    return response.json()["id"]


async def test_citizen_document_profile_flow() -> None:
    async with make_client() as client:
        user_id = await sign_in(client)
        await allow(client, "documents.processing")
        await allow(client, "profile.storage")
        document_id = await upload_income_document(client)

        values = (
            await client.post(
                f"{API}/profile/values/promote", json={"document_id": document_id}
            )
        ).json()
        assert {v["status"] for v in values} == {"unconfirmed"}

        full_name = next(v for v in values if v["field_key"] == "full_name")
        corrected = await client.post(
            f"{API}/profile/values/{full_name['id']}/correct",
            json={"value": "Asha Devi Sharma"},
        )
        assert corrected.json()["status"] == "confirmed"
        assert corrected.json()["correction_history"][0]["old_value"] == "Asha Devi"

        dob = next(v for v in values if v["field_key"] == "date_of_birth")
        confirmed = await client.post(f"{API}/profile/values/{dob['id']}/confirm")
        assert confirmed.json()["status"] == "confirmed"

        deleted = await client.delete(f"{API}/vault/documents/{document_id}")
        assert deleted.status_code == 204

        assert (
            await client.get(f"{API}/vault/documents/{document_id}/fields")
        ).status_code == 404
        with pytest.raises(FileNotFoundError):
            get_storage().read(uuid.UUID(user_id), uuid.UUID(document_id))

        remaining = (await client.get(f"{API}/profile/values")).json()
        assert len(remaining) == 7
        assert {v["status"] for v in remaining} == {"stale"}
        assert {v["stale_reason"] for v in remaining} == {
            "source_document_deleted"
        }


async def test_deleting_account_purges_stored_files() -> None:
    async with make_client() as client:
        user_id = await sign_in(client)
        await allow(client, "documents.processing")
        document_id = await upload_income_document(client)

        response = await client.delete(f"{API}/auth/account")
        assert response.status_code == 204

        with pytest.raises(FileNotFoundError):
            get_storage().read(uuid.UUID(user_id), uuid.UUID(document_id))


async def test_cross_user_delete_is_404_and_file_survives() -> None:
    async with make_client() as alice:
        alice_id = await sign_in(alice, "alice@example.com")
        await allow(alice, "documents.processing")
        document_id = await upload_income_document(alice)

        async with make_client() as bob:
            await sign_in(bob, "bob@example.com")
            await allow(bob, "documents.processing")

            assert (
                await bob.delete(f"{API}/vault/documents/{document_id}")
            ).status_code == 404

        assert (
            get_storage().read(uuid.UUID(alice_id), uuid.UUID(document_id))
            == INCOME_TEXT.encode()
        )
        assert (
            await alice.get(f"{API}/vault/documents/{document_id}")
        ).status_code == 200


async def test_document_content_sets_security_headers() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "documents.processing")
        document_id = await upload_income_document(client)

        response = await client.get(f"{API}/vault/documents/{document_id}/content")
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store, private"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["content-disposition"] == (
            'attachment; filename="income.txt"'
        )


async def test_document_content_disposition_sanitizes_filename() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "documents.processing")
        upload = await client.post(
            f"{API}/vault/documents",
            files={
                "file": (
                    'quote"name.txt',
                    INCOME_TEXT.encode(),
                    "text/plain",
                )
            },
        )
        assert upload.status_code == 201
        document_id = upload.json()["id"]

        response = await client.get(f"{API}/vault/documents/{document_id}/content")
        disposition = response.headers["content-disposition"]
        assert disposition.startswith("attachment; filename=")
        assert disposition.count('"') == 2
        assert "\r" not in disposition and "\n" not in disposition


async def test_delete_works_after_consent_withdrawal() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "documents.processing")
        document_id = await upload_income_document(client)

        grants = (await client.get(f"{API}/consent/grants")).json()
        active = next(
            g
            for g in grants
            if g["purpose"] == "documents.processing" and g["withdrawn_at"] is None
        )
        await client.post(f"{API}/consent/grants/{active['id']}/withdraw")

        assert (await client.get(f"{API}/vault/documents")).status_code == 403
        assert (
            await client.delete(f"{API}/vault/documents/{document_id}")
        ).status_code == 204


async def test_delete_requires_session() -> None:
    async with make_client() as client:
        response = await client.delete(f"{API}/vault/documents/{uuid.uuid4()}")
        assert response.status_code == 401


class DeleteFailingStorage:
    def __init__(self) -> None:
        self._real = get_storage()

    def save(
        self, user_id: uuid.UUID, document_id: uuid.UUID, data: bytes
    ) -> None:
        self._real.save(user_id, document_id, data)

    def read(self, user_id: uuid.UUID, document_id: uuid.UUID) -> bytes:
        return self._real.read(user_id, document_id)

    def delete(self, user_id: uuid.UUID, document_id: uuid.UUID) -> None:
        raise OSError("storage unavailable")


async def test_delete_document_keeps_record_when_unlink_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.modules.vault.routes as vault_routes

    storage = DeleteFailingStorage()
    monkeypatch.setattr(vault_routes, "get_storage", lambda: storage)

    async with make_client() as client:
        user_id = await sign_in(client)
        await allow(client, "documents.processing")
        document_id = await upload_income_document(client)

        response = await client.delete(f"{API}/vault/documents/{document_id}")
        assert response.status_code == 503

        assert (
            await client.get(f"{API}/vault/documents/{document_id}")
        ).status_code == 200
        assert (
            storage.read(uuid.UUID(user_id), uuid.UUID(document_id))
            == INCOME_TEXT.encode()
        )


async def test_audit_details_never_contain_document_content() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "documents.processing")
        await allow(client, "profile.storage")
        document_id = await upload_income_document(client)
        values = (
            await client.post(
                f"{API}/profile/values/promote", json={"document_id": document_id}
            )
        ).json()
        full_name = next(v for v in values if v["field_key"] == "full_name")
        await client.post(
            f"{API}/profile/values/{full_name['id']}/correct",
            json={"value": "Asha Devi Sharma"},
        )
        await client.delete(f"{API}/vault/documents/{document_id}")

    async with async_session_factory() as db:
        events = (await db.execute(select(AuditEvent))).scalars().all()
        rendered = str([event.details for event in events])
        assert "Asha Devi" not in rendered
        assert "income.txt" not in rendered
        actions = {event.action for event in events}
        assert {
            "document.uploaded",
            "document.processed",
            "document.deleted",
            "profile.values_promoted",
            "profile.value_corrected",
        } <= actions
