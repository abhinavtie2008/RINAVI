import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.modules.consent import schemas, service

router = APIRouter(prefix="/consent", tags=["consent"])


@router.get("/grants", response_model=list[schemas.ConsentRecordOut])
async def list_grants(
    user: CurrentUser, db: DbSession
) -> list[schemas.ConsentRecordOut]:
    records = await service.list_own_grants(db, user)
    return [schemas.ConsentRecordOut.model_validate(r) for r in records]


@router.post(
    "/grants",
    response_model=schemas.ConsentRecordOut,
    status_code=status.HTTP_201_CREATED,
)
async def grant(
    payload: schemas.ConsentGrantRequest, user: CurrentUser, db: DbSession
) -> schemas.ConsentRecordOut:
    record = await service.grant_consent(db, user, payload.purpose)
    await db.commit()
    return schemas.ConsentRecordOut.model_validate(record)


@router.post("/grants/{consent_id}/withdraw", response_model=schemas.ConsentRecordOut)
async def withdraw_grant(
    consent_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> schemas.ConsentRecordOut:
    record = await service.get_own_grant(db, user, consent_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Consent record not found"
        )
    await service.withdraw_record(db, record)
    await db.commit()
    return schemas.ConsentRecordOut.model_validate(record)
