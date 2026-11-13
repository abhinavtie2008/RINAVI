import uuid
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.applications import service as applications_service
from app.modules.applications.models import ApplicationDraft
from app.modules.identity.models import User, utcnow
from app.modules.locker import schemas
from app.modules.locker.models import ApplicationCase, CaseEvent, CaseStatus
from app.modules.vault.models import Document, DocumentStatus


class CaseError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


async def create_case(
    db: AsyncSession,
    user: User,
    draft: ApplicationDraft,
    snapshot: dict[str, Any],
    text: str,
) -> ApplicationCase:
    case = ApplicationCase(
        user_id=user.id,
        draft_id=draft.id,
        service_slug=draft.service_slug,
        service_name=draft.service_name,
        pack_version=draft.pack_version,
        packet_snapshot=snapshot,
        packet_text=text,
        status=CaseStatus.PREPARED,
    )
    db.add(case)
    await db.flush()
    db.add(CaseEvent(case_id=case.id, type="created", payload={}))
    await db.flush()
    return case


async def get_case_by_draft(
    db: AsyncSession, user: User, draft_id: uuid.UUID
) -> ApplicationCase | None:
    result = await db.execute(
        select(ApplicationCase).where(
            ApplicationCase.user_id == user.id,
            ApplicationCase.draft_id == draft_id,
        )
    )
    return result.scalar_one_or_none()


async def list_cases(db: AsyncSession, user: User) -> list[ApplicationCase]:
    result = await db.execute(
        select(ApplicationCase)
        .where(ApplicationCase.user_id == user.id)
        .order_by(ApplicationCase.created_at.desc())
    )
    return list(result.scalars())


async def get_case_for_user(
    db: AsyncSession, user: User, case_id: uuid.UUID
) -> ApplicationCase | None:
    result = await db.execute(
        select(ApplicationCase).where(
            ApplicationCase.id == case_id,
            ApplicationCase.user_id == user.id,
        )
    )
    return result.scalar_one_or_none()


async def list_events(db: AsyncSession, case: ApplicationCase) -> list[CaseEvent]:
    result = await db.execute(
        select(CaseEvent)
        .where(CaseEvent.case_id == case.id)
        .order_by(CaseEvent.created_at.asc())
    )
    return list(result.scalars())


def _apply_side_effect(
    case: ApplicationCase, event_type: str, payload: dict[str, Any]
) -> None:
    if event_type == "submitted":
        case.status = CaseStatus.SUBMITTED
        case.reference_number = payload["reference_number"]
    elif event_type == "acknowledged":
        case.status = CaseStatus.ACKNOWLEDGED
        case.acknowledgement_number = payload["acknowledgement_number"]
    elif event_type == "outcome_received":
        case.status = CaseStatus.OUTCOME_RECEIVED
        case.outcome_notes = payload["outcome_notes"]
    elif event_type == "abandoned":
        case.status = CaseStatus.ABANDONED
    elif event_type == "uncertain":
        case.status = CaseStatus.UNCERTAIN
    elif event_type == "deadline_updated":
        raw = payload["deadline_at"]
        case.deadline_at = date.fromisoformat(raw) if raw else None
    else:
        raise CaseError("unknown_event_type", f"Unknown event type: {event_type}")


async def record_event(
    db: AsyncSession,
    case: ApplicationCase,
    event_type: str,
    payload: dict[str, Any],
) -> CaseEvent:
    if event_type == "created":
        raise CaseError("unknown_event_type", "The created event is written by RINAVI.")
    _apply_side_effect(case, event_type, payload)
    case.updated_at = utcnow()
    event = CaseEvent(case_id=case.id, type=event_type, payload=payload)
    db.add(event)
    await db.flush()
    return event


def suggest_links(
    snapshot: dict[str, Any],
    template: dict[str, Any],
    documents: list[Document],
) -> list[dict[str, str]]:
    by_id = {str(document.id): document for document in documents}
    groups = template["checklist_groups"]
    suggestions: list[dict[str, str]] = []
    seen: set[str] = set()
    for evidence in snapshot["evidence"]:
        for entry in evidence["documents"]:
            document_id = entry["document_id"]
            if document_id in seen:
                continue
            document = by_id.get(document_id)
            if document is None or document.status != DocumentStatus.PROCESSED:
                continue
            classification = document.classification or ""
            for group in groups:
                accepted = group["accepted_classifications"]
                if accepted and classification not in accepted:
                    continue
                seen.add(document_id)
                suggestions.append(
                    {"document_id": document_id, "group_id": group["id"]}
                )
                break
    return suggestions


async def apply_again(
    db: AsyncSession, user: User, case: ApplicationCase
) -> tuple[ApplicationDraft, list[dict[str, str]]]:
    draft = await applications_service.create_draft(db, user, case.service_slug)
    document_ids = {
        entry["document_id"]
        for evidence in case.packet_snapshot["evidence"]
        for entry in evidence["documents"]
    }
    documents: list[Document] = []
    if document_ids:
        result = await db.execute(
            select(Document).where(
                Document.user_id == user.id,
                Document.id.in_([uuid.UUID(doc_id) for doc_id in document_ids]),
            )
        )
        documents = list(result.scalars())
    suggestions = suggest_links(
        case.packet_snapshot, draft.template_snapshot, documents
    )
    await db.flush()
    return draft, suggestions


async def case_out(db: AsyncSession, case: ApplicationCase) -> schemas.CaseOut:
    events = await list_events(db, case)
    return schemas.CaseOut(
        id=case.id,
        service_slug=case.service_slug,
        service_name=case.service_name,
        status=case.status,
        reference_number=case.reference_number,
        created_at=case.created_at,
        draft_id=case.draft_id,
        pack_version=case.pack_version,
        acknowledgement_number=case.acknowledgement_number,
        deadline_at=case.deadline_at,
        outcome_notes=case.outcome_notes,
        updated_at=case.updated_at,
        events=[
            schemas.CaseEventOut(
                id=event.id,
                type=event.type,
                payload=event.payload,
                created_at=event.created_at,
            )
            for event in events
        ],
        packet_snapshot=case.packet_snapshot,
    )
