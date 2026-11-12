import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.models import ExtractedField
from app.modules.identity.models import User, utcnow
from app.modules.profile.models import ProfileStatus, ProfileValue
from app.modules.vault.models import Document, DocumentStatus


class PromoteError(ValueError):
    pass


class TransitionError(ValueError):
    pass


async def list_values(db: AsyncSession, user: User) -> list[ProfileValue]:
    result = await db.execute(
        select(ProfileValue)
        .where(ProfileValue.user_id == user.id)
        .order_by(ProfileValue.field_key)
    )
    return list(result.scalars())


async def get_own_value(
    db: AsyncSession, user: User, value_id: uuid.UUID
) -> ProfileValue | None:
    result = await db.execute(
        select(ProfileValue).where(
            ProfileValue.id == value_id, ProfileValue.user_id == user.id
        )
    )
    return result.scalar_one_or_none()


async def promote_document(
    db: AsyncSession, user: User, document: Document
) -> list[ProfileValue]:
    if document.status != DocumentStatus.PROCESSED:
        raise PromoteError("Document has no extracted fields to promote")

    result = await db.execute(
        select(ExtractedField)
        .where(ExtractedField.document_id == document.id)
        .order_by(ExtractedField.field_key)
    )
    fields = list(result.scalars())

    existing_result = await db.execute(
        select(ProfileValue).where(ProfileValue.user_id == user.id)
    )
    by_key = {value.field_key: value for value in existing_result.scalars()}

    for field in fields:
        current = by_key.get(field.field_key)
        if current is not None and current.status == ProfileStatus.CONFIRMED:
            continue
        if current is None:
            current = ProfileValue(
                user_id=user.id, field_key=field.field_key, value=field.value
            )
            db.add(current)
            by_key[field.field_key] = current
        current.value = field.value
        current.status = ProfileStatus.UNCONFIRMED
        current.source_document_id = document.id
        current.source_locator = field.locator
        current.confidence = field.confidence
        current.stale_reason = None
        current.updated_at = utcnow()

    await db.flush()
    return sorted(by_key.values(), key=lambda value: value.field_key)


async def confirm_value(db: AsyncSession, value: ProfileValue) -> None:
    if value.status != ProfileStatus.UNCONFIRMED:
        raise TransitionError("Only unconfirmed values can be confirmed")
    value.status = ProfileStatus.CONFIRMED
    value.updated_at = utcnow()
    await db.flush()


async def correct_value(db: AsyncSession, value: ProfileValue, new_value: str) -> None:
    history = list(value.correction_history)
    history.append({"old_value": value.value, "corrected_at": utcnow().isoformat()})
    value.correction_history = history
    value.value = new_value
    value.status = ProfileStatus.CONFIRMED
    value.updated_at = utcnow()
    await db.flush()


async def reject_value(db: AsyncSession, value: ProfileValue) -> None:
    if value.status == ProfileStatus.CONFIRMED:
        raise TransitionError("Confirmed values cannot be rejected")
    await db.delete(value)
    await db.flush()


async def mark_values_stale(
    db: AsyncSession, user: User, document_id: uuid.UUID
) -> None:
    result = await db.execute(
        select(ProfileValue).where(
            ProfileValue.user_id == user.id,
            ProfileValue.source_document_id == document_id,
        )
    )
    for value in result.scalars():
        value.status = ProfileStatus.STALE
        value.stale_reason = "source_document_deleted"
        value.source_document_id = None
        value.source_locator = None
        value.updated_at = utcnow()
    await db.flush()
