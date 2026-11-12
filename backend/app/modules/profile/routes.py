import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import ConsentRequired, CurrentUser, DbSession
from app.modules.audit.service import emit_audit
from app.modules.profile import schemas, service
from app.modules.vault import service as vault_service

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get(
    "/values",
    response_model=list[schemas.ProfileValueOut],
    dependencies=[ConsentRequired("profile.storage")],
)
async def list_values(
    user: CurrentUser, db: DbSession
) -> list[schemas.ProfileValueOut]:
    values = await service.list_values(db, user)
    return [schemas.ProfileValueOut.model_validate(v) for v in values]


@router.post(
    "/values/promote",
    response_model=list[schemas.ProfileValueOut],
    dependencies=[ConsentRequired("profile.storage")],
)
async def promote(
    payload: schemas.PromoteRequest, user: CurrentUser, db: DbSession
) -> list[schemas.ProfileValueOut]:
    document = await vault_service.get_own_document(db, user, payload.document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    try:
        values = await service.promote_document(db, user, document)
    except service.PromoteError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    await emit_audit(
        db,
        actor_user_id=user.id,
        action="profile.values_promoted",
        resource_type="document",
        resource_id=str(document.id),
        details={"field_keys": sorted(value.field_key for value in values)},
    )
    await db.commit()
    return [schemas.ProfileValueOut.model_validate(v) for v in values]


@router.post(
    "/values/{value_id}/confirm",
    response_model=schemas.ProfileValueOut,
    dependencies=[ConsentRequired("profile.storage")],
)
async def confirm(
    value_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> schemas.ProfileValueOut:
    value = await service.get_own_value(db, user, value_id)
    if value is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    try:
        await service.confirm_value(db, value)
    except service.TransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    await emit_audit(
        db,
        actor_user_id=user.id,
        action="profile.value_confirmed",
        resource_type="profile_value",
        resource_id=str(value.id),
        details={"field_key": value.field_key},
    )
    await db.commit()
    return schemas.ProfileValueOut.model_validate(value)


@router.post(
    "/values/{value_id}/correct",
    response_model=schemas.ProfileValueOut,
    dependencies=[ConsentRequired("profile.storage")],
)
async def correct(
    value_id: uuid.UUID,
    payload: schemas.CorrectRequest,
    user: CurrentUser,
    db: DbSession,
) -> schemas.ProfileValueOut:
    value = await service.get_own_value(db, user, value_id)
    if value is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    await service.correct_value(db, value, payload.value)
    await emit_audit(
        db,
        actor_user_id=user.id,
        action="profile.value_corrected",
        resource_type="profile_value",
        resource_id=str(value.id),
        details={"field_key": value.field_key},
    )
    await db.commit()
    return schemas.ProfileValueOut.model_validate(value)


@router.post("/values/{value_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
async def reject(
    value_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> None:
    value = await service.get_own_value(db, user, value_id)
    if value is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    field_key = value.field_key
    try:
        await service.reject_value(db, value)
    except service.TransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    await emit_audit(
        db,
        actor_user_id=user.id,
        action="profile.value_rejected",
        resource_type="profile_value",
        resource_id=str(value_id),
        details={"field_key": field_key},
    )
    await db.commit()
