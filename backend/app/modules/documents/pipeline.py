from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.extraction import (
    classify,
    extract_candidates,
    extract_text_from_pdf,
    extract_text_from_txt,
)
from app.modules.documents.models import ExtractedField
from app.modules.identity.models import utcnow
from app.modules.vault.models import Document, DocumentStatus
from app.modules.vault.storage import StorageBackend

_IMAGE_TYPES = {"image/png", "image/jpeg"}


async def process_document(
    db: AsyncSession, storage: StorageBackend, document: Document
) -> None:
    document.status = DocumentStatus.PROCESSING
    data = storage.read(document.user_id, document.id)

    if document.content_type in _IMAGE_TYPES:
        document.status = DocumentStatus.NEEDS_ATTENTION
        document.note = "ocr_not_configured"
        await db.flush()
        return

    try:
        if document.content_type == "application/pdf":
            text = extract_text_from_pdf(data)
        else:
            text = extract_text_from_txt(data)
    except Exception:
        document.status = DocumentStatus.NEEDS_ATTENTION
        document.note = "extraction_failed"
        await db.flush()
        return

    if not text.strip():
        document.status = DocumentStatus.NEEDS_ATTENTION
        document.note = "no_text_layer"
        await db.flush()
        return

    candidates = extract_candidates(text)
    if not candidates:
        document.status = DocumentStatus.NEEDS_ATTENTION
        document.note = "no_fields_detected"
        document.classification = "unsupported"
        await db.flush()
        return

    await db.execute(
        delete(ExtractedField).where(ExtractedField.document_id == document.id)
    )
    for candidate in candidates:
        db.add(
            ExtractedField(
                document_id=document.id,
                field_key=candidate.field_key,
                value=candidate.value,
                confidence=candidate.confidence,
                locator=candidate.locator,
            )
        )
    document.classification = classify(candidates)
    document.status = DocumentStatus.PROCESSED
    document.note = None
    document.processed_at = utcnow()
    await db.flush()
