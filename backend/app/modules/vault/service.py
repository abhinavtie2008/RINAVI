import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.models import ExtractedField
from app.modules.identity.models import User
from app.modules.vault.models import Document, DocumentStatus
from app.modules.vault.storage import StorageBackend


async def create_document(
    db: AsyncSession,
    storage: StorageBackend,
    user: User,
    *,
    filename: str,
    content_type: str,
    data: bytes,
) -> Document:
    document = Document(
        user_id=user.id,
        original_filename=filename[:255],
        content_type=content_type,
        size_bytes=len(data),
        status=DocumentStatus.QUARANTINED,
    )
    db.add(document)
    await db.flush()
    storage.save(user.id, document.id, data)
    return document


async def list_documents(db: AsyncSession, user: User) -> list[Document]:
    result = await db.execute(
        select(Document)
        .where(Document.user_id == user.id)
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars())


async def get_own_document(
    db: AsyncSession, user: User, document_id: uuid.UUID
) -> Document | None:
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.user_id == user.id
        )
    )
    return result.scalar_one_or_none()


async def list_fields(db: AsyncSession, document: Document) -> list[ExtractedField]:
    result = await db.execute(
        select(ExtractedField)
        .where(ExtractedField.document_id == document.id)
        .order_by(ExtractedField.field_key)
    )
    return list(result.scalars())
