import uuid
from datetime import timedelta
from typing import Any

from httpx import ASGITransport, AsyncClient, Cookies
from sqlalchemy import select

from app.core.db import async_session_factory
from app.main import app
from app.modules.audit.models import AuditEvent
from app.modules.identity.models import utcnow
from app.modules.locker.models import ApplicationCase, CaseEvent

API = "/api/v1"

INCOME_TEXT = "Annual Income: Rs. 1,20,000\n"
IDENTITY_TEXT = "Applicant Name: Asha Devi\nAadhaar: 1234 5678 9012\n"


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
    return response.json()["id"]


async def create_case_row(
    user_id: str,
    service_slug: str = "delhi-income-certificate",
    service_name: str = "Income Certificate (Delhi)",
    snapshot: dict[str, Any] | None = None,
    created_offset_minutes: int = 0,
) -> str:
    async with async_session_factory() as db:
        case = ApplicationCase(
            user_id=uuid.UUID(user_id),
            service_slug=service_slug,
            service_name=service_name,
            pack_version="1.0.0",
            packet_snapshot=snapshot if snapshot is not None else {"fields": [], "evidence": []},
            packet_text="RINAVI — application draft (NOT a submission)",
            created_at=utcnow() + timedelta(minutes=created_offset_minutes),
        )
        db.add(case)
        await db.flush()
        db.add(CaseEvent(case_id=case.id, type="created", payload={}))
        await db.commit()
        return str(case.id)


async def test_locker_requires_active_consent() -> None:
    async with make_client() as client:
        await sign_in(client)
        assert (await client.get(f"{API}/locker/cases")).status_code == 403


async def test_list_cases_returns_summaries_newest_first() -> None:
    async with make_client() as client:
        user_id = await sign_in(client)
        await allow(client, "locker.tracking")
        await create_case_row(user_id, service_name="Older case")
        await create_case_row(
            user_id, service_name="Newer case", created_offset_minutes=5
        )

        response = await client.get(f"{API}/locker/cases")

        assert response.status_code == 200
        names = [case["service_name"] for case in response.json()]
        assert names == ["Newer case", "Older case"]
        assert "packet_snapshot" not in response.json()[0]


async def test_get_case_returns_events_and_404s_for_others() -> None:
    async with make_client() as client:
        owner_id = await sign_in(client)
        await allow(client, "locker.tracking")
        case_id = await create_case_row(owner_id)

        response = await client.get(f"{API}/locker/cases/{case_id}")
        assert response.status_code == 200
        assert response.json()["id"] == case_id

        assert (
            await client.get(f"{API}/locker/cases/{uuid.uuid4()}")
        ).status_code == 404

        await sign_in(client, email="other@example.com")
        await allow(client, "locker.tracking")
        foreign = await client.get(f"{API}/locker/cases/{case_id}")
        assert foreign.status_code == 404
        assert foreign.json()["detail"] == "Case not found"


async def test_record_event_updates_status_and_journal() -> None:
    async with make_client() as client:
        user_id = await sign_in(client)
        await allow(client, "locker.tracking")
        case_id = await create_case_row(user_id)

        submitted = await client.post(
            f"{API}/locker/cases/{case_id}/events",
            json={"type": "submitted", "reference_number": "REF-42"},
        )
        assert submitted.status_code == 200
        body = submitted.json()
        assert body["status"] == "submitted"
        assert body["reference_number"] == "REF-42"
        assert [event["type"] for event in body["events"]] == ["created", "submitted"]
        assert body["events"][1]["payload"] == {"reference_number": "REF-42"}

        acknowledged = await client.post(
            f"{API}/locker/cases/{case_id}/events",
            json={"type": "acknowledged", "acknowledgement_number": "ACK-7"},
        )
        assert acknowledged.status_code == 200
        assert acknowledged.json()["status"] == "acknowledged"
        assert acknowledged.json()["acknowledgement_number"] == "ACK-7"

        outcome = await client.post(
            f"{API}/locker/cases/{case_id}/events",
            json={"type": "outcome_received", "outcome_notes": "Certificate issued."},
        )
        assert outcome.status_code == 200
        assert outcome.json()["status"] == "outcome_received"
        assert outcome.json()["outcome_notes"] == "Certificate issued."

        async with async_session_factory() as db:
            result = await db.execute(
                select(AuditEvent).where(
                    AuditEvent.action == "locker.event_recorded"
                )
            )
            audits = result.scalars().all()
            assert len(audits) == 3
            assert {audit.details["event_type"] for audit in audits} == {
                "submitted",
                "acknowledged",
                "outcome_received",
            }


async def test_record_event_normalizes_empty_strings_to_null() -> None:
    async with make_client() as client:
        user_id = await sign_in(client)
        await allow(client, "locker.tracking")
        case_id = await create_case_row(user_id)

        response = await client.post(
            f"{API}/locker/cases/{case_id}/events",
            json={"type": "submitted", "reference_number": ""},
        )

        assert response.status_code == 200
        assert response.json()["reference_number"] is None
        assert response.json()["events"][1]["payload"] == {"reference_number": None}


async def test_record_event_deadline_set_and_clear() -> None:
    async with make_client() as client:
        user_id = await sign_in(client)
        await allow(client, "locker.tracking")
        case_id = await create_case_row(user_id)

        set_response = await client.post(
            f"{API}/locker/cases/{case_id}/events",
            json={"type": "deadline_updated", "deadline_at": "2026-12-01"},
        )
        assert set_response.status_code == 200
        assert set_response.json()["deadline_at"] == "2026-12-01"
        assert set_response.json()["status"] == "prepared"

        clear_response = await client.post(
            f"{API}/locker/cases/{case_id}/events",
            json={"type": "deadline_updated", "deadline_at": None},
        )
        assert clear_response.status_code == 200
        assert clear_response.json()["deadline_at"] is None


async def test_record_event_abandoned_and_uncertain() -> None:
    async with make_client() as client:
        user_id = await sign_in(client)
        await allow(client, "locker.tracking")
        case_id = await create_case_row(user_id)

        abandoned = await client.post(
            f"{API}/locker/cases/{case_id}/events", json={"type": "abandoned"}
        )
        assert abandoned.status_code == 200
        assert abandoned.json()["status"] == "abandoned"

        uncertain = await client.post(
            f"{API}/locker/cases/{case_id}/events", json={"type": "uncertain"}
        )
        assert uncertain.status_code == 200
        assert uncertain.json()["status"] == "uncertain"


async def test_record_event_rejects_created_unknown_and_bad_payloads() -> None:
    async with make_client() as client:
        user_id = await sign_in(client)
        await allow(client, "locker.tracking")
        case_id = await create_case_row(user_id)

        assert (
            await client.post(
                f"{API}/locker/cases/{case_id}/events", json={"type": "created"}
            )
        ).status_code == 422
        assert (
            await client.post(
                f"{API}/locker/cases/{case_id}/events", json={"type": "teleported"}
            )
        ).status_code == 422
        assert (
            await client.post(
                f"{API}/locker/cases/{case_id}/events",
                json={"type": "deadline_updated", "deadline_at": "2026-13-99"},
            )
        ).status_code == 422
        assert (
            await client.post(
                f"{API}/locker/cases/{case_id}/events",
                json={"type": "outcome_received", "outcome_notes": "x" * 2001},
            )
        ).status_code == 422


async def test_apply_again_creates_draft_with_suggested_links() -> None:
    async with make_client() as client:
        user_id = await sign_in(client)
        await allow(client, "locker.tracking")
        await allow(client, "documents.processing")
        income_id = await upload(client, INCOME_TEXT, "income.txt")
        identity_id = await upload(client, IDENTITY_TEXT, "identity.txt")
        case_id = await create_case_row(
            user_id,
            snapshot={
                "fields": [],
                "evidence": [
                    {
                        "group_id": "income_evidence",
                        "group_label": "Income evidence",
                        "documents": [
                            {"document_id": income_id, "filename": "income.txt"},
                            {"document_id": identity_id, "filename": "identity.txt"},
                        ],
                    }
                ],
            },
        )

        response = await client.post(f"{API}/locker/cases/{case_id}/apply-again")

        assert response.status_code == 201
        body = response.json()
        assert body["draft"]["service_slug"] == "delhi-income-certificate"
        assert body["draft"]["validation"]
        assert body["suggested_links"] == [
            {"document_id": income_id, "group_id": "residence_proof"},
            {"document_id": identity_id, "group_id": "identity_proof"},
        ]

        async with async_session_factory() as db:
            result = await db.execute(
                select(AuditEvent).where(AuditEvent.action == "locker.apply_again")
            )
            audit = result.scalars().one()
            assert audit.details["case_id"] == case_id
            assert audit.details["draft_id"] == body["draft"]["id"]


async def test_apply_again_404s() -> None:
    async with make_client() as client:
        user_id = await sign_in(client)
        await allow(client, "locker.tracking")

        unknown = await client.post(
            f"{API}/locker/cases/{uuid.uuid4()}/apply-again"
        )
        assert unknown.status_code == 404
        assert unknown.json()["detail"] == "Case not found"

        gone_id = await create_case_row(
            user_id, service_slug="gone-service", snapshot={"fields": [], "evidence": []}
        )
        gone = await client.post(f"{API}/locker/cases/{gone_id}/apply-again")
        assert gone.status_code == 404
        assert gone.json()["detail"] == "Service not found"
