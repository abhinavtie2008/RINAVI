from httpx import ASGITransport, AsyncClient, Cookies
from sqlalchemy import select

from app.core.db import async_session_factory
from app.main import app
from app.modules.audit.models import AuditEvent

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
        assert confirmed.json()["status"] == "confirmed"


async def test_applications_require_active_consent() -> None:
    async with make_client() as client:
        await sign_in(client)
        assert (await client.get(f"{API}/applications/drafts")).status_code == 403


async def test_draft_lifecycle_prepares_valid_export() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "documents.processing")
        await allow(client, "profile.storage")
        await allow(client, "applications.preparation")
        income_id = await upload(client, INCOME_TEXT, "income.txt")
        identity_id = await upload(client, IDENTITY_TEXT, "identity.txt")
        await promote_and_confirm(client, income_id)

        created = await client.post(
            f"{API}/applications/drafts",
            json={"service_slug": "delhi-income-certificate"},
        )
        assert created.status_code == 201
        draft = created.json()
        assert draft["values"]["applicant_name"]["origin"] == "profile"
        assert draft["declaration_confirmed"] is False
        assert (
            await client.get(f"{API}/applications/drafts/{draft['id']}/export")
        ).status_code == 409

        purpose = await client.put(
            f"{API}/applications/drafts/{draft['id']}/fields/purpose",
            json={"value": "Scholarship application"},
        )
        assert purpose.status_code == 200
        assert purpose.json()["values"]["purpose"]["origin"] == "citizen"
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

        exported = await client.get(f"{API}/applications/drafts/{draft['id']}/export")
        assert exported.status_code == 200
        text = exported.json()["text"]
        assert "NOT a submission" in text
        assert "Asha Devi" in text
        assert "income.txt" in text
        assert "Declaration: CONFIRMED" in text
        drafts = (await client.get(f"{API}/applications/drafts")).json()
        assert [d["id"] for d in drafts] == [draft["id"]]
        assert (
            await client.delete(f"{API}/applications/drafts/{draft['id']}")
        ).status_code == 204
        assert (await client.get(f"{API}/applications/drafts")).json() == []


async def test_draft_error_cases_and_cross_user_isolation() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "documents.processing")
        await allow(client, "applications.preparation")
        identity_id = await upload(client, IDENTITY_TEXT, "identity.txt")
        assert (
            await client.post(
                f"{API}/applications/drafts", json={"service_slug": "no-such-service"}
            )
        ).status_code == 404
        draft = (
            await client.post(
                f"{API}/applications/drafts",
                json={"service_slug": "delhi-income-certificate"},
            )
        ).json()
        assert (
            await client.put(
                f"{API}/applications/drafts/{draft['id']}/fields/no_such_field",
                json={"value": "x"},
            )
        ).status_code == 404
        assert (
            await client.put(
                f"{API}/applications/drafts/{draft['id']}/documents/{identity_id}",
                json={"group_id": "no_such_group"},
            )
        ).status_code == 422
        assert (
            await client.put(
                f"{API}/applications/drafts/{draft['id']}/documents/{identity_id}",
                json={"group_id": "income_evidence"},
            )
        ).status_code == 422
        async with make_client() as other:
            await sign_in(other, "other@example.com")
            await allow(other, "applications.preparation")
            assert (
                await other.get(f"{API}/applications/drafts/{draft['id']}")
            ).status_code == 404


async def test_drafts_require_session() -> None:
    async with make_client() as client:
        assert (await client.get(f"{API}/applications/drafts")).status_code == 401


async def test_audit_events_never_contain_draft_values() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "documents.processing")
        await allow(client, "profile.storage")
        await allow(client, "applications.preparation")
        income_id = await upload(client, INCOME_TEXT, "income.txt")
        await promote_and_confirm(client, income_id)
        draft = (
            await client.post(
                f"{API}/applications/drafts",
                json={"service_slug": "delhi-income-certificate"},
            )
        ).json()
        await client.put(
            f"{API}/applications/drafts/{draft['id']}/fields/purpose",
            json={"value": "Scholarship application"},
        )
    async with async_session_factory() as db:
        events = (await db.execute(select(AuditEvent))).scalars().all()
        rendered = str([event.details for event in events])
        assert "Asha Devi" not in rendered
        assert "Scholarship" not in rendered
        assert "application.draft_created" in {event.action for event in events}
