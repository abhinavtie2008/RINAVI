import logging

import pytest

from app.core.db import async_session_factory
from app.modules.documents import pipeline
from app.modules.identity import service as identity_service
from app.modules.vault.models import Document, DocumentStatus


class FakeStorage:
    def read(self, user_id: object, document_id: object) -> bytes:
        return b"%PDF-1.7 fake content"

    def save(self, user_id: object, document_id: object, data: bytes) -> None:
        pass

    def delete(self, user_id: object, document_id: object) -> None:
        pass

    def purge_user(self, user_id: object) -> None:
        pass


async def test_extraction_failure_logs_reason_and_marks_document(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def boom(_data: bytes) -> str:
        raise ValueError("pdf parse failed")

    monkeypatch.setattr(pipeline, "extract_text_from_pdf", boom)
    caplog.set_level(logging.ERROR)

    async with async_session_factory() as db:
        user = await identity_service.get_or_create_user(db, "citizen@example.com")
        await db.commit()
        document = Document(
            user_id=user.id,
            original_filename="broken.pdf",
            content_type="application/pdf",
            size_bytes=0,
        )
        db.add(document)
        await db.flush()
        document_id = str(document.id)

        await pipeline.process_document(db, FakeStorage(), document)
        await db.commit()

        assert document.status == DocumentStatus.NEEDS_ATTENTION
        assert document.note == "extraction_failed: ValueError"

    assert any(
        "Document processing failed" in r.getMessage()
        and document_id in r.getMessage()
        and "ValueError" in r.getMessage()
        for r in caplog.records
        if r.levelno >= logging.ERROR
    )
