from app.core.db import async_session_factory
from app.modules.applications.models import ApplicationDraft
from app.modules.applications.service import build_packet
from app.modules.identity.models import User
from app.modules.vault.models import Document, DocumentStatus

TEMPLATE = {
    "fields": [
        {
            "id": "applicant_name",
            "label": "Applicant name",
            "binding": "full_name",
            "required": True,
            "format": "text",
        },
        {
            "id": "purpose",
            "label": "Purpose of certificate",
            "binding": None,
            "required": True,
            "format": "text",
        },
    ],
    "declaration": {"required": True, "text": "I declare."},
    "checklist_groups": [
        {
            "id": "income_evidence",
            "label": "Income evidence",
            "requirement": "at_least_one",
            "accepted_classifications": ["income"],
        }
    ],
    "guidance": {
        "official_channel_steps": ["Register on the portal."],
        "not_a_submission_notice": "Review only.",
    },
}


async def make_packet_inputs(db, service_slug: str = "delhi-income-certificate"):
    user = User(email="citizen@example.com", display_name="Citizen")
    db.add(user)
    await db.flush()
    document = Document(
        user_id=user.id,
        original_filename="income.txt",
        content_type="text/plain",
        size_bytes=10,
        status=DocumentStatus.PROCESSED,
        classification="income",
    )
    db.add(document)
    await db.flush()
    draft = ApplicationDraft(
        user_id=user.id,
        service_slug=service_slug,
        service_name="Income Certificate (Delhi)",
        pack_version="1.0.0",
        template_snapshot=TEMPLATE,
        values={
            "applicant_name": {"value": "Asha Devi", "origin": "profile"},
            "purpose": {"value": "Scholarship", "origin": "citizen"},
        },
        document_links={"income_evidence": [str(document.id)]},
        declaration_confirmed=True,
    )
    db.add(draft)
    await db.flush()
    return user, draft, document


async def test_build_packet_snapshots_fields_evidence_and_fixed_copy() -> None:
    async with async_session_factory() as db:
        user, draft, document = await make_packet_inputs(db)

        snapshot, text = await build_packet(db, user, draft)

        assert snapshot["fields"] == [
            {
                "id": "applicant_name",
                "label": "Applicant name",
                "value": "Asha Devi",
                "origin": "profile",
            },
            {
                "id": "purpose",
                "label": "Purpose of certificate",
                "value": "Scholarship",
                "origin": "citizen",
            },
        ]
        assert snapshot["evidence"] == [
            {
                "group_id": "income_evidence",
                "group_label": "Income evidence",
                "documents": [
                    {"document_id": str(document.id), "filename": "income.txt"}
                ],
            }
        ]
        assert snapshot["declaration"] == {"required": True, "text": "I declare."}
        assert snapshot["official_channel_steps"] == ["Register on the portal."]
        assert (
            snapshot["processing_time"]
            == "Indicative only: around 14 days after submission; not a guarantee"
        )
        assert snapshot["not_a_submission_notice"] == "Review only."
        assert snapshot["portal_down_guidance"] == (
            "If the portal is unavailable, nothing here changes. Your packet "
            "stays in the locker. Try the official channel again later — "
            "RINAVI does not submit on your behalf."
        )
        assert snapshot["acknowledgement_guidance"] == (
            "No acknowledgement yet? Some portals send receipts later. Check "
            "your email and the portal, then record the acknowledgement number "
            "here when it arrives."
        )
        assert "NOT a submission" in text


async def test_build_packet_processing_time_is_null_when_service_left_catalog() -> None:
    async with async_session_factory() as db:
        user, draft, _document = await make_packet_inputs(
            db, service_slug="gone-service"
        )

        snapshot, _text = await build_packet(db, user, draft)

        assert snapshot["processing_time"] is None
