import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.consent.models import ConsentRecord
from app.modules.identity.models import User, utcnow


async def grant_consent(db: AsyncSession, user: User, purpose: str) -> ConsentRecord:
    await withdraw_consent(db, user, purpose)
    record = ConsentRecord(
        user_id=user.id,
        purpose=purpose,
        policy_version=get_settings().consent_policy_version,
    )
    db.add(record)
    await db.flush()
    return record


async def withdraw_consent(db: AsyncSession, user: User, purpose: str) -> None:
    result = await db.execute(
        select(ConsentRecord).where(
            ConsentRecord.user_id == user.id,
            ConsentRecord.purpose == purpose,
            ConsentRecord.withdrawn_at.is_(None),
        )
    )
    for record in result.scalars():
        await withdraw_record(db, record)


async def withdraw_record(db: AsyncSession, record: ConsentRecord) -> None:
    record.withdrawn_at = utcnow()
    await db.flush()


async def list_own_grants(db: AsyncSession, user: User) -> list[ConsentRecord]:
    result = await db.execute(
        select(ConsentRecord)
        .where(ConsentRecord.user_id == user.id)
        .order_by(ConsentRecord.granted_at.desc())
    )
    return list(result.scalars())


async def get_own_grant(
    db: AsyncSession, user: User, consent_id: uuid.UUID
) -> ConsentRecord | None:
    result = await db.execute(
        select(ConsentRecord).where(
            ConsentRecord.id == consent_id,
            ConsentRecord.user_id == user.id,
        )
    )
    return result.scalar_one_or_none()


async def has_active_consent(db: AsyncSession, user: User, purpose: str) -> bool:
    result = await db.execute(
        select(ConsentRecord).where(
            ConsentRecord.user_id == user.id,
            ConsentRecord.purpose == purpose,
            ConsentRecord.withdrawn_at.is_(None),
        )
    )
    # .first() tolerates duplicate active grants from racing requests
    # instead of raising MultipleResultsFound.
    return result.scalars().first() is not None
