import uuid
from datetime import date
from typing import Any

import pytest

from app.core.db import async_session_factory
from app.modules.applications.models import ApplicationDraft
from app.modules.catalog.loader import CatalogError
from app.modules.identity.models import User
from app.modules.locker.models import ApplicationCase
from app.modules.locker.service import (
    CaseError,
    apply_again,
    create_case,
    get_case_by_draft,
    get_case_for_user,
    list_events,
    record_event,
    suggest_links,
)
from app.modules.vault.models import Document, DocumentStatus

DOC_A = "11111111-1111-1111-1111-111111111111"
DOC_B = "22222222-2222-2222-2222-222222222222"
DOC_C = "33333333-3333-3333-3333-333333333333"
DOC_D = "44444444-4444-4444-4444-444444444444"

SNAPSHOT: dict[str, Any] = {
    "fields": [],
    "evidence": [
        {
            "group_id": "income_evidence",
            "group_label": "Income evidence",
            "documents": [{"document_id": DOC_A, "filename": "income.txt"}],
        }
    ],
    "declaration": {"required": True, "text": "I declare."},
    "official_channel_steps": ["Register on the portal."],
    "processing_time": "Indicative only",
    "not_a_submission_notice": "Review only.",
    "portal_down_guidance": "Portal down.",
    "acknowledgement_guidance": "No ack yet.",
}


async def make_user(db, email: str = "citizen@example.com") -> User:
    user = User(email=email, display_name="Citizen")
    db.add(user)
    await db.flush()
    return user


async def make_draft(db, user: User) -> ApplicationDraft:
    draft = ApplicationDraft(
        user_id=user.id,
        service_slug="delhi-income-certificate",
        service_name="Income Certificate (Delhi)",
        pack_version="1.0.0",
        template_snapshot={"fields": [], "declaration": {}, "checklist_groups": [], "guidance": {}},
        values={},
        document_links={},
        declaration_confirmed=False,
    )
    db.add(draft)
    await db.flush()
    return draft


async def make_case(db, user: User) -> ApplicationCase:
    draft = await make_draft(db, user)
    return await create_case(db, user, draft, dict(SNAPSHOT), "packet text")


def make_document(
    doc_id: str,
    classification: str | None,
    status: str = DocumentStatus.PROCESSED,
) -> Document:
    return Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.uuid4(),
        original_filename=f"{doc_id}.txt",
        content_type="text/plain",
        size_bytes=10,
        status=status,
        classification=classification,
    )


async def test_create_case_sets_prepared_and_writes_created_event() -> None:
    async with async_session_factory() as db:
        user = await make_user(db)
        draft = await make_draft(db, user)
        case = await create_case(db, user, draft, {"fields": []}, "packet text")
        await db.commit()

        assert case.status == "prepared"
        assert case.draft_id == draft.id
        assert case.packet_text == "packet text"

    async with async_session_factory() as db:
        events = await list_events(db, case)
        assert [event.type for event in events] == ["created"]
        assert events[0].payload == {}


async def test_record_event_submitted_updates_status_and_reference() -> None:
    async with async_session_factory() as db:
        user = await make_user(db)
        case = await make_case(db, user)
        await record_event(db, case, "submitted", {"reference_number": "REF-123"})
        assert case.status == "submitted"
        assert case.reference_number == "REF-123"


async def test_record_event_acknowledged_and_outcome_update_columns() -> None:
    async with async_session_factory() as db:
        user = await make_user(db)
        case = await make_case(db, user)

        await record_event(
            db, case, "acknowledged", {"acknowledgement_number": "ACK-9"}
        )
        assert case.status == "acknowledged"
        assert case.acknowledgement_number == "ACK-9"

        await record_event(
            db, case, "outcome_received", {"outcome_notes": "Certificate issued."}
        )
        assert case.status == "outcome_received"
        assert case.outcome_notes == "Certificate issued."


async def test_record_event_abandoned_and_uncertain_update_status() -> None:
    async with async_session_factory() as db:
        user = await make_user(db)
        case = await make_case(db, user)

        await record_event(db, case, "abandoned", {})
        assert case.status == "abandoned"

        await record_event(db, case, "uncertain", {})
        assert case.status == "uncertain"


async def test_record_event_deadline_updated_sets_and_clears_without_status_change() -> None:
    async with async_session_factory() as db:
        user = await make_user(db)
        case = await make_case(db, user)

        await record_event(db, case, "deadline_updated", {"deadline_at": "2026-12-01"})
        assert case.deadline_at == date(2026, 12, 1)
        assert case.status == "prepared"

        await record_event(db, case, "deadline_updated", {"deadline_at": None})
        assert case.deadline_at is None


async def test_record_event_rejects_created_and_unknown_types() -> None:
    async with async_session_factory() as db:
        user = await make_user(db)
        case = await make_case(db, user)

        with pytest.raises(CaseError):
            await record_event(db, case, "created", {})
        with pytest.raises(CaseError):
            await record_event(db, case, "teleported", {})


async def test_get_case_lookups_are_scoped_to_the_owner() -> None:
    async with async_session_factory() as db:
        owner = await make_user(db)
        other = await make_user(db, email="other@example.com")
        draft = await make_draft(db, owner)
        case = await create_case(db, owner, draft, dict(SNAPSHOT), "packet text")

        assert await get_case_for_user(db, owner, case.id) is not None
        assert await get_case_for_user(db, other, case.id) is None
        assert await get_case_by_draft(db, owner, draft.id) is not None
        assert await get_case_by_draft(db, other, draft.id) is None


def test_suggest_links_filters_and_maps_in_snapshot_order() -> None:
    snapshot = {
        "evidence": [
            {
                "group_id": "old_group",
                "group_label": "Old evidence",
                "documents": [
                    {"document_id": DOC_A, "filename": "a.txt"},
                    {"document_id": DOC_A, "filename": "a.txt"},
                    {"document_id": DOC_B, "filename": "b.txt"},
                    {"document_id": DOC_C, "filename": "c.txt"},
                    {"document_id": DOC_D, "filename": "d.txt"},
                ],
            }
        ]
    }
    template = {
        "checklist_groups": [
            {
                "id": "identity_proof",
                "label": "Identity proof",
                "accepted_classifications": ["identity"],
            },
            {
                "id": "income_evidence",
                "label": "Income evidence",
                "accepted_classifications": ["income"],
            },
            {
                "id": "any_evidence",
                "label": "Anything",
                "accepted_classifications": [],
            },
        ]
    }
    documents = [
        make_document(DOC_A, "income"),
        make_document(DOC_B, "identity"),
        make_document(DOC_C, None),
        make_document(DOC_D, "income", status=DocumentStatus.QUARANTINED),
    ]

    suggestions = suggest_links(snapshot, template, documents)

    assert suggestions == [
        {"document_id": DOC_A, "group_id": "income_evidence"},
        {"document_id": DOC_B, "group_id": "identity_proof"},
        {"document_id": DOC_C, "group_id": "any_evidence"},
    ]


async def test_apply_again_creates_draft_from_catalog() -> None:
    async with async_session_factory() as db:
        user = await make_user(db)
        case = await make_case(db, user)

        new_draft, suggestions = await apply_again(db, user, case)

        assert new_draft.service_slug == "delhi-income-certificate"
        assert new_draft.id != case.draft_id
        assert suggestions == []


async def test_apply_again_raises_catalog_error_when_service_left_catalog() -> None:
    async with async_session_factory() as db:
        user = await make_user(db)
        case = await make_case(db, user)
        case.service_slug = "gone-service"

        with pytest.raises(CatalogError):
            await apply_again(db, user, case)
