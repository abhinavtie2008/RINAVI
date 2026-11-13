import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ConsentRequired, CurrentUser, DbSession
from app.modules.applications import schemas, service
from app.modules.applications.models import ApplicationDraft
from app.modules.applications.service import DraftError
from app.modules.applications.validator import validate_draft
from app.modules.audit.service import emit_audit
from app.modules.catalog.loader import CatalogError
from app.modules.identity.models import User

router = APIRouter(prefix="/applications", tags=["applications"])
CONSENT = ConsentRequired("applications.preparation")


async def _get_draft_or_404(
    db: AsyncSession, user: User, draft_id: uuid.UUID
) -> ApplicationDraft:
    draft = await service.get_own_draft(db, user, draft_id)
    if draft is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found"
        )
    return draft


def _raise_draft_error(error: DraftError) -> None:
    http_status = (
        status.HTTP_404_NOT_FOUND
        if error.code == "unknown_field"
        else status.HTTP_422_UNPROCESSABLE_CONTENT
    )
    raise HTTPException(status_code=http_status, detail=error.code) from error


@router.post(
    "/drafts",
    response_model=schemas.DraftOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[CONSENT],
)
async def create_draft(
    payload: schemas.DraftCreateIn, user: CurrentUser, db: DbSession
) -> schemas.DraftOut:
    try:
        draft = await service.create_draft(db, user, payload.service_slug)
    except CatalogError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        ) from exc
    await emit_audit(
        db,
        actor_user_id=user.id,
        action="application.draft_created",
        resource_type="application_draft",
        resource_id=str(draft.id),
        details={"service_slug": draft.service_slug},
    )
    await db.commit()
    return await service.draft_out(db, user, draft)


@router.get(
    "/drafts", response_model=list[schemas.DraftOut], dependencies=[CONSENT]
)
async def list_drafts(user: CurrentUser, db: DbSession) -> list[schemas.DraftOut]:
    drafts = await service.list_drafts(db, user)
    return [await service.draft_out(db, user, draft) for draft in drafts]


@router.get(
    "/drafts/{draft_id}", response_model=schemas.DraftOut, dependencies=[CONSENT]
)
async def get_draft(
    draft_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> schemas.DraftOut:
    draft = await _get_draft_or_404(db, user, draft_id)
    return await service.draft_out(db, user, draft)


@router.put(
    "/drafts/{draft_id}/fields/{field_id}",
    response_model=schemas.DraftOut,
    dependencies=[CONSENT],
)
async def update_field(
    draft_id: uuid.UUID,
    field_id: str,
    payload: schemas.FieldUpdateIn,
    user: CurrentUser,
    db: DbSession,
) -> schemas.DraftOut:
    draft = await _get_draft_or_404(db, user, draft_id)
    try:
        service.set_field_value(draft, field_id, payload.value)
    except DraftError as exc:
        _raise_draft_error(exc)
    await emit_audit(
        db,
        actor_user_id=user.id,
        action="application.draft_field_updated",
        resource_type="application_draft",
        resource_id=str(draft.id),
        details={"field_id": field_id},
    )
    await db.commit()
    return await service.draft_out(db, user, draft)


@router.post(
    "/drafts/{draft_id}/refresh",
    response_model=schemas.DraftOut,
    dependencies=[CONSENT],
)
async def refresh_draft(
    draft_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> schemas.DraftOut:
    draft = await _get_draft_or_404(db, user, draft_id)
    await service.refresh_draft(db, user, draft)
    await emit_audit(
        db,
        actor_user_id=user.id,
        action="application.draft_refreshed",
        resource_type="application_draft",
        resource_id=str(draft.id),
        details={"service_slug": draft.service_slug},
    )
    await db.commit()
    return await service.draft_out(db, user, draft)


@router.put(
    "/drafts/{draft_id}/documents/{document_id}",
    response_model=schemas.DraftOut,
    dependencies=[CONSENT],
)
async def link_document(
    draft_id: uuid.UUID,
    document_id: uuid.UUID,
    payload: schemas.DocumentLinkIn,
    user: CurrentUser,
    db: DbSession,
) -> schemas.DraftOut:
    draft = await _get_draft_or_404(db, user, draft_id)
    try:
        await service.link_document(db, user, draft, document_id, payload.group_id)
    except DraftError as exc:
        _raise_draft_error(exc)
    await emit_audit(
        db,
        actor_user_id=user.id,
        action="application.document_linked",
        resource_type="application_draft",
        resource_id=str(draft.id),
        details={"group_id": payload.group_id, "document_id": str(document_id)},
    )
    await db.commit()
    return await service.draft_out(db, user, draft)


@router.delete(
    "/drafts/{draft_id}/documents/{document_id}",
    response_model=schemas.DraftOut,
    dependencies=[CONSENT],
)
async def unlink_document(
    draft_id: uuid.UUID,
    document_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> schemas.DraftOut:
    draft = await _get_draft_or_404(db, user, draft_id)
    service.unlink_document(draft, document_id)
    await emit_audit(
        db,
        actor_user_id=user.id,
        action="application.document_unlinked",
        resource_type="application_draft",
        resource_id=str(draft.id),
        details={"document_id": str(document_id)},
    )
    await db.commit()
    return await service.draft_out(db, user, draft)


@router.put(
    "/drafts/{draft_id}/declaration",
    response_model=schemas.DraftOut,
    dependencies=[CONSENT],
)
async def update_declaration(
    draft_id: uuid.UUID,
    payload: schemas.DeclarationIn,
    user: CurrentUser,
    db: DbSession,
) -> schemas.DraftOut:
    draft = await _get_draft_or_404(db, user, draft_id)
    service.set_declaration(draft, payload.confirmed)
    await emit_audit(
        db,
        actor_user_id=user.id,
        action="application.declaration_updated",
        resource_type="application_draft",
        resource_id=str(draft.id),
        details={"confirmed": payload.confirmed},
    )
    await db.commit()
    return await service.draft_out(db, user, draft)


@router.get(
    "/drafts/{draft_id}/export",
    response_model=schemas.ExportOut,
    dependencies=[CONSENT],
)
async def export_draft(
    draft_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> schemas.ExportOut:
    draft = await _get_draft_or_404(db, user, draft_id)
    profile, states = await service.collect_validation_inputs(db, user, draft)
    issues = validate_draft(
        draft.template_snapshot,
        draft.values,
        draft.declaration_confirmed,
        draft.document_links,
        states,
        profile,
    )
    if issues:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Draft has unresolved issues",
        )
    text = await service.build_export(db, user, draft)
    await emit_audit(
        db,
        actor_user_id=user.id,
        action="application.draft_exported",
        resource_type="application_draft",
        resource_id=str(draft.id),
        details={"service_slug": draft.service_slug},
    )
    await db.commit()
    return schemas.ExportOut(text=text)


@router.delete(
    "/drafts/{draft_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[CONSENT],
)
async def delete_draft(
    draft_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> None:
    draft = await _get_draft_or_404(db, user, draft_id)
    service_slug = draft.service_slug
    await db.delete(draft)
    await emit_audit(
        db,
        actor_user_id=user.id,
        action="application.draft_deleted",
        resource_type="application_draft",
        resource_id=str(draft_id),
        details={"service_slug": service_slug},
    )
    await db.commit()
