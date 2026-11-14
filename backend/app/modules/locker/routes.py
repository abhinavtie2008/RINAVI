import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import ConsentRequired, CurrentUser, DbSession
from app.modules.applications import service as applications_service
from app.modules.audit.service import emit_audit
from app.modules.catalog.loader import CatalogError
from app.modules.locker import schemas, service
from app.modules.locker.models import ApplicationCase
from app.modules.locker.service import CaseError

router = APIRouter(prefix="/locker", tags=["locker"])
CONSENT = ConsentRequired("locker.tracking")


def _clean(value: str | None) -> str | None:
    return value if value else None


async def _get_case_or_404(
    db: DbSession, user: CurrentUser, case_id: uuid.UUID
) -> ApplicationCase:
    case = await service.get_case_for_user(db, user, case_id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Case not found"
        )
    return case


@router.get(
    "/cases", response_model=list[schemas.CaseSummaryOut], dependencies=[CONSENT]
)
async def list_cases(
    user: CurrentUser, db: DbSession
) -> list[schemas.CaseSummaryOut]:
    cases = await service.list_cases(db, user)
    return [
        schemas.CaseSummaryOut(
            id=case.id,
            service_slug=case.service_slug,
            service_name=case.service_name,
            status=case.status,
            reference_number=case.reference_number,
            created_at=case.created_at,
        )
        for case in cases
    ]


@router.get(
    "/cases/{case_id}", response_model=schemas.CaseOut, dependencies=[CONSENT]
)
async def get_case(
    case_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> schemas.CaseOut:
    case = await _get_case_or_404(db, user, case_id)
    return await service.case_out(db, case)


@router.post(
    "/cases/{case_id}/events",
    response_model=schemas.CaseOut,
    dependencies=[CONSENT],
)
async def record_case_event(
    case_id: uuid.UUID,
    payload: schemas.CaseEventIn,
    user: CurrentUser,
    db: DbSession,
) -> schemas.CaseOut:
    case = await _get_case_or_404(db, user, case_id)
    if isinstance(payload, schemas.SubmittedEventIn):
        event_payload = {"reference_number": _clean(payload.reference_number)}
    elif isinstance(payload, schemas.AcknowledgedEventIn):
        event_payload = {
            "acknowledgement_number": _clean(payload.acknowledgement_number)
        }
    elif isinstance(payload, schemas.OutcomeReceivedEventIn):
        event_payload = {"outcome_notes": _clean(payload.outcome_notes)}
    elif isinstance(payload, schemas.DeadlineUpdatedEventIn):
        event_payload = {
            "deadline_at": payload.deadline_at.isoformat()
            if payload.deadline_at
            else None
        }
    else:
        event_payload = {}
    try:
        await service.record_event(db, case, payload.type, event_payload)
    except CaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=exc.code
        ) from exc
    await emit_audit(
        db,
        actor_user_id=user.id,
        action="locker.event_recorded",
        resource_type="application_case",
        resource_id=str(case.id),
        details={"event_type": payload.type},
    )
    await db.commit()
    return await service.case_out(db, case)


@router.post(
    "/cases/{case_id}/apply-again",
    response_model=schemas.ApplyAgainOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[CONSENT],
)
async def apply_again(
    case_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> schemas.ApplyAgainOut:
    case = await _get_case_or_404(db, user, case_id)
    try:
        draft, suggested_links = await service.apply_again(db, user, case)
    except CatalogError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        ) from exc
    await emit_audit(
        db,
        actor_user_id=user.id,
        action="locker.apply_again",
        resource_type="application_case",
        resource_id=str(case.id),
        details={"case_id": str(case.id), "draft_id": str(draft.id)},
    )
    await db.commit()
    return schemas.ApplyAgainOut(
        draft=await applications_service.draft_out(db, user, draft),
        suggested_links=[
            schemas.SuggestionOut(
                document_id=item["document_id"], group_id=item["group_id"]
            )
            for item in suggested_links
        ],
    )
