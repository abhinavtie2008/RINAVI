import uuid

from httpx import ASGITransport, AsyncClient, Cookies
from sqlalchemy import select

from app.core.db import async_session_factory
from app.main import app
from app.modules.audit.models import AuditEvent
from app.modules.locker.models import ApplicationCase

API = "/api/v1"

INCOME_TEXT = (
    "Applicant Name: Asha Devi\n"
    "Father's Name: Rajesh Devi\n"
    "Date of Birth: 12/03/1994\n"
    "Gender: Female\n"
    "Address: 14, Nehru Colony, Example Nagar\n"
    "Annual Income: Rs. 1,20,000\n"
)
IDENTITY_TEXT = (
    "Applicant Name: Asha Devi\n"
    "Address: 14, Nehru Colony, Example Nagar\n"
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


async def upload(client: AsyncClient, text: str, filename: str) -> str:
    response = await client.post(
        f"{API}/vault/documents",
        files={"file": (filename, text.encode(), "text/plain")},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "processed"
    return response.json()["id"]


async def promote_and_confirm(client: AsyncClient, document_id: str) -> None:
    response = await client.post(
        f"{API}/profile/values/promote", json={"document_id": document_id}
    )
    assert response.status_code == 200
    for value in response.json():
        confirmed = await client.post(f"{API}/profile/values/{value['id']}/confirm")
        assert confirmed.status_code == 200


async def make_completable_draft(client: AsyncClient) -> dict:
    await allow(client, "documents.processing")
    await allow(client, "profile.storage")
    income_id = await upload(client, INCOME_TEXT, "income.txt")
    identity_id = await upload(client, IDENTITY_TEXT, "identity.txt")
    await promote_and_confirm(client, income_id)
    created = await client.post(
        f"{API}/applications/drafts",
        json={"service_slug": "delhi-income-certificate"},
    )
    assert created.status_code == 201
    draft = created.json()
    purpose = await client.put(
        f"{API}/applications/drafts/{draft['id']}/fields/purpose",
        json={"value": "Scholarship application"},
    )
    assert purpose.status_code == 200
    for group_id, document_id in [
        ("income_evidence", income_id),
        ("identity_proof", identity_id),
        ("residence_proof", identity_id),
    ]:
        linked = await client.put(
            f"{API}/applications/drafts/{draft['id']}/documents/{document_id}",
            json={"group_id": group_id},
        )
        assert linked.status_code == 200
    declared = await client.put(
        f"{API}/applications/drafts/{draft['id']}/declaration",
        json={"confirmed": True},
    )
    assert declared.status_code == 200
    assert declared.json()["validation"] == []
    return declared.json()


async def test_complete_requires_active_consent() -> None:
    async with make_client() as client:
        await sign_in(client)
        response = await client.post(
            f"{API}/applications/drafts/{uuid.uuid4()}/complete"
        )
        assert response.status_code == 403


async def test_complete_rejects_draft_with_unresolved_issues() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "applications.preparation")
        created = await client.post(
            f"{API}/applications/drafts",
            json={"service_slug": "delhi-income-certificate"},
        )
        assert created.status_code == 201

        response = await client.post(
            f"{API}/applications/drafts/{created.json()['id']}/complete"
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "Draft has unresolved issues"


async def test_complete_creates_prepared_case_with_frozen_packet() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "applications.preparation")
        await allow(client, "locker.tracking")
        draft = await make_completable_draft(client)

        response = await client.post(
            f"{API}/applications/drafts/{draft['id']}/complete"
        )

        assert response.status_code == 200
        case = response.json()
        assert case["status"] == "prepared"
        assert case["draft_id"] == draft["id"]
        assert case["service_slug"] == "delhi-income-certificate"
        assert [event["type"] for event in case["events"]] == ["created"]
        snapshot = case["packet_snapshot"]
        assert snapshot["declaration"]["text"].startswith("I declare")
        fields = {field["id"]: field for field in snapshot["fields"]}
        assert fields["purpose"]["value"] == "Scholarship application"
        assert snapshot["processing_time"].startswith("Indicative only")
        assert "RINAVI does not submit on your behalf" in snapshot["portal_down_guidance"]

        # Mutating the draft afterwards must not change the frozen packet.
        changed = await client.put(
            f"{API}/applications/drafts/{draft['id']}/fields/purpose",
            json={"value": "Changed purpose"},
        )
        assert changed.status_code == 200

        async with async_session_factory() as db:
            stored = await db.get(ApplicationCase, uuid.UUID(case["id"]))
            assert stored is not None
            frozen_fields = {
                field["id"]: field for field in stored.packet_snapshot["fields"]
            }
            assert frozen_fields["purpose"]["value"] == "Scholarship application"
            result = await db.execute(
                select(AuditEvent).where(
                    AuditEvent.action == "application.case_created"
                )
            )
            assert result.scalars().one_or_none() is not None


async def test_complete_is_idempotent() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "applications.preparation")
        draft = await make_completable_draft(client)

        first = await client.post(f"{API}/applications/drafts/{draft['id']}/complete")
        second = await client.post(f"{API}/applications/drafts/{draft['id']}/complete")

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["id"] == second.json()["id"]
        assert [event["type"] for event in second.json()["events"]] == ["created"]


async def test_case_survives_draft_deletion() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "applications.preparation")
        await allow(client, "locker.tracking")
        draft = await make_completable_draft(client)
        created = await client.post(
            f"{API}/applications/drafts/{draft['id']}/complete"
        )
        assert created.status_code == 200
        case_id = created.json()["id"]

        deleted = await client.delete(f"{API}/applications/drafts/{draft['id']}")
        assert deleted.status_code == 204

        async with async_session_factory() as db:
            stored = await db.get(ApplicationCase, uuid.UUID(case_id))
            assert stored is not None
            assert stored.draft_id is None
            assert stored.packet_snapshot["official_channel_steps"]
