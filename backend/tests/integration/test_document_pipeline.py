import os
import threading
import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient, Cookies
from sqlalchemy import select

from app.core.db import async_session_factory
from app.main import app
from app.modules.audit.models import AuditEvent
from app.modules.documents.models import ExtractedField
from tests.factories import make_multipage_pdf, make_text_pdf

API = "/api/v1"

INCOME_TEXT = (
    "Applicant Name: Asha Devi\n"
    "Father's Name: Rajesh Devi\n"
    "Date of Birth: 12/03/1994\n"
    "Gender: Female\n"
    "Address: 14, Nehru Colony, Example Nagar\n"
    "Annual Income: Rs. 1,20,000\n"
    "Aadhaar: 1234 5678 9012\n"
)


def make_client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies=Cookies(),
    )


async def sign_in(client: AsyncClient, email: str = "citizen@example.com") -> None:
    response = await client.post(f"{API}/auth/dev-signin", json={"email": email})
    assert response.status_code == 200


async def allow_documents(client: AsyncClient) -> None:
    response = await client.post(
        f"{API}/consent/grants", json={"purpose": "documents.processing"}
    )
    assert response.status_code == 201


async def upload(
    client: AsyncClient,
    *,
    name: str,
    content: bytes,
    content_type: str,
):
    return await client.post(
        f"{API}/vault/documents",
        files={"file": (name, content, content_type)},
    )


async def test_txt_document_is_processed_with_fields() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow_documents(client)

        response = await upload(
            client, name="income.txt", content=INCOME_TEXT.encode(), content_type="text/plain"
        )

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "processed"
        assert body["classification"] == "income"
        assert body["processed_at"] is not None

        fields = await client.get(f"{API}/vault/documents/{body['id']}/fields")
        assert fields.status_code == 200
        by_key = {f["field_key"]: f for f in fields.json()}
        assert set(by_key) == {
            "full_name",
            "father_name",
            "date_of_birth",
            "gender",
            "address",
            "annual_income",
        }
        assert "aadhaar_number" not in by_key
        assert by_key["full_name"]["value"] == "Asha Devi"
        assert by_key["full_name"]["confidence"] == "high"
        assert by_key["full_name"]["locator"] == "line 1"

        # The Aadhaar line is still recognised (so the document classifies as
        # identity), but the digits must not be stored at rest either.
        async with async_session_factory() as db:
            stored = (
                await db.execute(
                    select(ExtractedField).where(
                        ExtractedField.document_id == uuid.UUID(body["id"])
                    )
                )
            ).scalars()
            aadhaar = [
                field for field in stored if field.field_key == "aadhaar_number"
            ]
        assert len(aadhaar) == 1
        assert aadhaar[0].value == "[REDACTED]"
        assert "123456789012" not in aadhaar[0].value


async def test_pdf_with_text_layer_is_processed() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow_documents(client)

        pdf = make_text_pdf(["Applicant Name: Asha Devi", "Annual Income: Rs. 1,20,000"])
        response = await upload(
            client, name="income.pdf", content=pdf, content_type="application/pdf"
        )

        assert response.status_code == 201
        assert response.json()["status"] == "processed"
        fields = await client.get(f"{API}/vault/documents/{response.json()['id']}/fields")
        keys = {f["field_key"] for f in fields.json()}
        assert {"full_name", "annual_income"} <= keys


async def test_pdf_over_page_limit_is_marked_needs_attention() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow_documents(client)

        pdf = make_multipage_pdf([["Applicant Name: Asha Devi"]] * 101)
        response = await upload(
            client, name="large.pdf", content=pdf, content_type="application/pdf"
        )

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "needs_attention"
        assert body["note"] == "page_limit_exceeded"


async def test_pdf_over_text_limit_is_marked_needs_attention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The production limit is 2 MB; a small one exercises the same pipeline
    # branch without generating a 2 MB document in the test.
    monkeypatch.setattr(
        "app.modules.documents.extraction.TEXT_LIMIT_CHARS", 64, raising=False
    )
    async with make_client() as client:
        await sign_in(client)
        await allow_documents(client)

        pdf = make_multipage_pdf(
            [
                ["Applicant Name: Asha Devi"],
                ["Annual Income: Rs. 1,20,000"],
                ["Address: 14, Nehru Colony, Example Nagar"],
            ]
        )
        response = await upload(
            client, name="income.pdf", content=pdf, content_type="application/pdf"
        )

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "needs_attention"
        assert body["note"] == "text_limit_exceeded"


async def test_pdf_parse_timeout_is_reported_as_needs_attention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The production deadline is 20s; zero exercises the same pipeline branch
    # without building a document that is genuinely slow to parse.
    monkeypatch.setattr(
        "app.modules.documents.extraction.PARSE_TIMEOUT_SECONDS", 0.0
    )
    async with make_client() as client:
        await sign_in(client)
        await allow_documents(client)

        pdf = make_text_pdf(["Applicant Name: Asha Devi"])
        response = await upload(
            client, name="income.pdf", content=pdf, content_type="application/pdf"
        )

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "needs_attention"
        assert body["note"] == "parse_timeout"


async def test_pdf_extraction_runs_off_the_event_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main_thread = threading.get_ident()
    extraction_threads: list[int] = []

    def capture(data: bytes) -> tuple[str, str | None]:
        extraction_threads.append(threading.get_ident())
        return "Applicant Name: Asha Devi\n", None

    monkeypatch.setattr(
        "app.modules.documents.pipeline.extract_text_from_pdf", capture
    )

    async with make_client() as client:
        await sign_in(client)
        await allow_documents(client)

        pdf = make_text_pdf(["Applicant Name: Asha Devi"])
        response = await upload(
            client, name="income.pdf", content=pdf, content_type="application/pdf"
        )

    assert response.status_code == 201
    assert response.json()["status"] == "processed"
    assert extraction_threads
    assert extraction_threads[0] != main_thread


async def test_retry_reports_the_same_page_limit() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow_documents(client)

        pdf = make_multipage_pdf([["Applicant Name: Asha Devi"]] * 101)
        uploaded = await upload(
            client, name="large.pdf", content=pdf, content_type="application/pdf"
        )
        assert uploaded.json()["note"] == "page_limit_exceeded"

        retried = await client.post(
            f"{API}/vault/documents/{uploaded.json()['id']}/retry"
        )

        assert retried.status_code == 200
        assert retried.json()["status"] == "needs_attention"
        assert retried.json()["note"] == "page_limit_exceeded"


async def test_image_is_marked_needs_attention_without_ocr() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow_documents(client)

        png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
        response = await upload(
            client, name="scan.png", content=png, content_type="image/png"
        )

        body = response.json()
        assert body["status"] == "needs_attention"
        assert body["note"] == "ocr_not_configured"
        fields = await client.get(f"{API}/vault/documents/{body['id']}/fields")
        assert fields.json() == []


async def test_text_without_fields_needs_attention() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow_documents(client)

        response = await upload(
            client,
            name="notes.txt",
            content=b"Just a shopping list.\n",
            content_type="text/plain",
        )

        body = response.json()
        assert body["status"] == "needs_attention"
        assert body["note"] == "no_fields_detected"
        assert body["classification"] == "unsupported"


async def test_retry_replaces_fields_without_duplicates() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow_documents(client)
        uploaded = await upload(
            client, name="income.txt", content=INCOME_TEXT.encode(), content_type="text/plain"
        )
        document_id = uploaded.json()["id"]

        retried = await client.post(f"{API}/vault/documents/{document_id}/retry")

        assert retried.status_code == 200
        assert retried.json()["status"] == "processed"
        fields = await client.get(f"{API}/vault/documents/{document_id}/fields")
        assert len(fields.json()) == 6


async def test_fields_are_scoped_to_the_owner() -> None:
    async with make_client() as alice:
        await sign_in(alice, "alice@example.com")
        await allow_documents(alice)
        uploaded = await upload(
            alice, name="income.txt", content=INCOME_TEXT.encode(), content_type="text/plain"
        )
        document_id = uploaded.json()["id"]

        async with make_client() as bob:
            await sign_in(bob, "bob@example.com")
            await allow_documents(bob)

            assert (
                await bob.get(f"{API}/vault/documents/{document_id}/fields")
            ).status_code == 404


def _storage_root() -> Path:
    return Path(os.environ["RINAVI_STORAGE_DIR"])


def _stored_blobs(document_id: str) -> list[Path]:
    return list(_storage_root().rglob(f"{document_id}.bin"))


def _all_blobs() -> list[Path]:
    return list(_storage_root().rglob("*.bin"))


async def test_missing_blob_is_reported_not_crashed() -> None:
    # An interrupted delete or a lost volume leaves the row without its bytes.
    # Reading it unconditionally used to answer 500 for a document the citizen
    # can still see in the vault.
    async with make_client() as client:
        await sign_in(client)
        await allow_documents(client)
        uploaded = await upload(
            client, name="income.txt", content=INCOME_TEXT.encode(), content_type="text/plain"
        )
        document_id = uploaded.json()["id"]
        for blob in _stored_blobs(document_id):
            blob.unlink()

        retried = await client.post(f"{API}/vault/documents/{document_id}/retry")

        assert retried.status_code == 200
        assert retried.json()["status"] == "needs_attention"
        assert retried.json()["note"] == "content_unavailable"


async def test_failed_upload_leaves_no_orphaned_blob(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def explode(*args: object, **kwargs: object) -> None:
        raise RuntimeError("processing exploded")

    monkeypatch.setattr("app.modules.vault.routes.process_document", explode)

    async with make_client() as client:
        await sign_in(client)
        await allow_documents(client)
        with pytest.raises(RuntimeError):
            await upload(
                client,
                name="income.txt",
                content=INCOME_TEXT.encode(),
                content_type="text/plain",
            )

    # The row is rolled back with the session; the bytes would have stayed on
    # disk with nothing left to reach or erase them.
    assert _all_blobs() == []


async def test_extractor_crash_is_reported_as_needs_attention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def explode(text: str) -> None:
        raise ValueError("unparseable text")

    monkeypatch.setattr("app.modules.documents.pipeline.extract_candidates", explode)

    async with make_client() as client:
        await sign_in(client)
        await allow_documents(client)

        response = await upload(
            client, name="income.txt", content=INCOME_TEXT.encode(), content_type="text/plain"
        )

        assert response.status_code == 201
        assert response.json()["status"] == "needs_attention"
        assert response.json()["note"] == "extraction_failed: ValueError"


async def test_processed_event_is_audited() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow_documents(client)
        await upload(
            client, name="income.txt", content=INCOME_TEXT.encode(), content_type="text/plain"
        )

    async with async_session_factory() as db:
        events = (await db.execute(select(AuditEvent))).scalars().all()
        processed = [e for e in events if e.action == "document.processed"]
        assert len(processed) == 1
        assert processed[0].details["classification"] == "income"
