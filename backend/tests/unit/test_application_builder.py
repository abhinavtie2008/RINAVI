import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_factory
from app.modules.applications import service
from app.modules.applications.models import ApplicationDraft
from app.modules.applications.service import DraftError
from app.modules.catalog.loader import CatalogError, FormField, ServicePack
from app.modules.identity.models import User
from app.modules.profile.models import ProfileStatus, ProfileValue
from app.modules.vault.models import Document, DocumentStatus

SLUG = "delhi-income-certificate"

RESTRICTED_TEMPLATE = {
    "fields": [
        {
            "id": "applicant_name",
            "label": "Applicant name",
            "binding": "full_name",
            "required": True,
            "format": "text",
        },
        {
            "id": "aadhaar_number",
            "label": "Aadhaar number",
            "binding": "aadhaar_number",
            "required": True,
            "format": "aadhaar",
        },
        {
            "id": "portal_aadhaar",
            "label": "Aadhaar number (enter at the portal)",
            "binding": None,
            "required": True,
            "format": "aadhaar",
        },
    ],
    "declaration": {"required": True, "text": "I declare."},
    "checklist_groups": [],
    "guidance": {
        "official_channel_steps": ["Register on the portal."],
        "not_a_submission_notice": "Review only.",
    },
}


def restricted_draft(user: User) -> ApplicationDraft:
    return ApplicationDraft(
        user_id=user.id,
        service_slug=SLUG,
        service_name="Income Certificate (Delhi)",
        pack_version="1.0.0",
        template_snapshot=RESTRICTED_TEMPLATE,
        values={
            "applicant_name": {"value": "Asha Devi", "origin": "citizen"},
            "aadhaar_number": {"value": "123456789012", "origin": "citizen"},
        },
        document_links={},
        declaration_confirmed=True,
    )


async def make_user(db: AsyncSession) -> User:
    user = User(email="citizen@example.com", display_name="Citizen")
    db.add(user)
    await db.flush()
    return user


async def make_document(
    db: AsyncSession,
    user: User,
    *,
    status: DocumentStatus = DocumentStatus.PROCESSED,
    classification: str | None = "income",
) -> Document:
    document = Document(
        user_id=user.id,
        original_filename="income.txt",
        content_type="text/plain",
        size_bytes=12,
        status=status,
        classification=classification,
    )
    db.add(document)
    await db.flush()
    return document


async def test_create_draft_snapshots_pack_and_seeds_confirmed_profile() -> None:
    async with async_session_factory() as db:
        user = await make_user(db)
        db.add(
            ProfileValue(
                user_id=user.id,
                field_key="full_name",
                value="Asha Devi",
                status=ProfileStatus.CONFIRMED,
            )
        )
        db.add(
            ProfileValue(
                user_id=user.id,
                field_key="address",
                value="14, Nehru Colony",
                status=ProfileStatus.UNCONFIRMED,
            )
        )
        await db.flush()

        draft = await service.create_draft(db, user, SLUG)

        assert draft.pack_version == "1.0.0"
        assert draft.service_name == "Income Certificate (Delhi)"
        assert draft.values["applicant_name"] == {
            "value": "Asha Devi",
            "origin": "profile",
        }
        assert "residence_address" not in draft.values
        assert draft.declaration_confirmed is False
        assert draft.template_snapshot["guidance"]["not_a_submission_notice"]
        assert draft.template_snapshot["fields"][0]["id"] == "applicant_name"


async def test_create_draft_rejects_unknown_service() -> None:
    async with async_session_factory() as db:
        user = await make_user(db)
        with pytest.raises(CatalogError):
            await service.create_draft(db, user, "no-such-service")


async def test_set_field_value_sets_citizen_origin_and_clears_on_empty() -> None:
    async with async_session_factory() as db:
        user = await make_user(db)
        draft = await service.create_draft(db, user, SLUG)

        service.set_field_value(draft, "purpose", "Scholarship application")
        assert draft.values["purpose"] == {
            "value": "Scholarship application",
            "origin": "citizen",
        }
        service.set_field_value(draft, "purpose", "")
        assert "purpose" not in draft.values
        with pytest.raises(DraftError) as exc_info:
            service.set_field_value(draft, "no_such_field", "x")
        assert exc_info.value.code == "unknown_field"


async def test_refresh_updates_profile_origin_but_never_citizen_origin() -> None:
    async with async_session_factory() as db:
        user = await make_user(db)
        db.add(
            ProfileValue(
                user_id=user.id,
                field_key="full_name",
                value="Asha Devi",
                status=ProfileStatus.CONFIRMED,
            )
        )
        await db.flush()
        draft = await service.create_draft(db, user, SLUG)
        service.set_field_value(draft, "father_or_husband_name", "Rajesh Devi")
        profile_value = (
            await db.execute(
                select(ProfileValue).where(ProfileValue.field_key == "full_name")
            )
        ).scalar_one()
        profile_value.value = "Asha Devi Sharma"

        await service.refresh_draft(db, user, draft)

        assert draft.values["applicant_name"] == {
            "value": "Asha Devi Sharma",
            "origin": "profile",
        }
        assert draft.values["father_or_husband_name"] == {
            "value": "Rajesh Devi",
            "origin": "citizen",
        }


async def test_link_document_enforces_group_classification_and_status() -> None:
    async with async_session_factory() as db:
        user = await make_user(db)
        draft = await service.create_draft(db, user, SLUG)
        income = await make_document(db, user)
        identity = await make_document(db, user, classification="identity")
        pending = await make_document(db, user, status=DocumentStatus.QUARANTINED)

        with pytest.raises(DraftError) as exc_info:
            await service.link_document(db, user, draft, income.id, "no_such_group")
        assert exc_info.value.code == "unknown_group"
        with pytest.raises(DraftError) as exc_info:
            await service.link_document(db, user, draft, pending.id, "income_evidence")
        assert exc_info.value.code == "document_not_available"
        with pytest.raises(DraftError) as exc_info:
            await service.link_document(db, user, draft, identity.id, "income_evidence")
        assert exc_info.value.code == "document_not_suitable"

        await service.link_document(db, user, draft, income.id, "income_evidence")
        await service.link_document(db, user, draft, identity.id, "identity_proof")
        await service.link_document(db, user, draft, identity.id, "residence_proof")
        assert draft.document_links["income_evidence"] == [str(income.id)]
        assert draft.document_links["residence_proof"] == [str(identity.id)]
        service.unlink_document(draft, income.id)
        assert draft.document_links["income_evidence"] == []


async def test_collect_validation_inputs_marks_missing_documents_unavailable() -> None:
    async with async_session_factory() as db:
        user = await make_user(db)
        draft = await service.create_draft(db, user, SLUG)
        ghost = uuid.uuid4()
        draft.document_links = {"income_evidence": [str(ghost)]}
        await db.flush()

        profile, states = await service.collect_validation_inputs(db, user, draft)

        assert profile == {}
        assert states == {str(ghost): "unavailable"}


async def test_collect_validation_inputs_tolerates_unparseable_document_id() -> None:
    # document_links is a JSON column, so a malformed value must degrade to
    # "unavailable" instead of raising on every read of the draft.
    async with async_session_factory() as db:
        user = await make_user(db)
        draft = await service.create_draft(db, user, SLUG)
        draft.document_links = {"income_evidence": ["not-a-uuid"]}
        await db.flush()

        profile, states = await service.collect_validation_inputs(db, user, draft)

        assert profile == {}
        assert states == {"not-a-uuid": "unavailable"}


async def test_build_export_tolerates_unparseable_document_id() -> None:
    async with async_session_factory() as db:
        user = await make_user(db)
        draft = await service.create_draft(db, user, SLUG)
        draft.document_links = {"income_evidence": ["not-a-uuid"]}
        await db.flush()

        text = await service.build_export(db, user, draft)

        assert "not-a-uuid" in text


async def test_build_packet_tolerates_unparseable_document_id() -> None:
    async with async_session_factory() as db:
        user = await make_user(db)
        draft = await service.create_draft(db, user, SLUG)
        draft.document_links = {"income_evidence": ["not-a-uuid"]}
        await db.flush()

        snapshot, _text = await service.build_packet(db, user, draft)

        evidence = {e["group_id"]: e for e in snapshot["evidence"]}
        assert evidence["income_evidence"]["documents"] == [
            {"document_id": "not-a-uuid", "filename": "not-a-uuid"}
        ]


def test_public_snapshot_and_values_hide_restricted_bindings() -> None:
    snapshot = service._public_snapshot(RESTRICTED_TEMPLATE)

    assert [field["id"] for field in snapshot["fields"]] == ["applicant_name"]
    values = service._public_values(
        snapshot,
        {
            "applicant_name": {"value": "Asha Devi", "origin": "citizen"},
            "aadhaar_number": {"value": "123456789012", "origin": "citizen"},
        },
    )
    assert values == {
        "applicant_name": {"value": "Asha Devi", "origin": "citizen"}
    }
    assert RESTRICTED_TEMPLATE["fields"][1]["id"] == "aadhaar_number"


def test_snapshot_omits_aadhaar_format_fields_without_binding() -> None:
    pack = ServicePack(
        pack_version="1.0.0",
        service_slug=SLUG,
        guidance=RESTRICTED_TEMPLATE["guidance"],
        checklist_groups=[],
        fields=[
            FormField(
                id="applicant_name",
                label="Applicant name",
                binding="full_name",
                required=True,
                format="text",
            ),
            FormField(
                id="portal_aadhaar",
                label="Aadhaar number",
                binding=None,
                required=True,
                format="aadhaar",
            ),
        ],
        declaration=RESTRICTED_TEMPLATE["declaration"],
    )

    snapshot = service._snapshot(pack)

    assert [field["id"] for field in snapshot["fields"]] == ["applicant_name"]


def test_set_field_value_rejects_restricted_fields() -> None:
    draft = ApplicationDraft(
        user_id=uuid.uuid4(),
        service_slug=SLUG,
        service_name="Income Certificate (Delhi)",
        pack_version="1.0.0",
        template_snapshot=RESTRICTED_TEMPLATE,
        values={},
        document_links={},
        declaration_confirmed=False,
    )

    for field_id in ("aadhaar_number", "portal_aadhaar"):
        with pytest.raises(DraftError) as exc_info:
            service.set_field_value(draft, field_id, "123456789012")
        assert exc_info.value.code == "restricted_field"
    assert draft.values == {}


async def test_draft_out_hides_restricted_fields_values_and_issues() -> None:
    async with async_session_factory() as db:
        user = await make_user(db)
        draft = restricted_draft(user)
        db.add(draft)
        await db.flush()

        out = await service.draft_out(db, user, draft)

        assert [field["id"] for field in out.template_snapshot["fields"]] == [
            "applicant_name"
        ]
        assert set(out.values) == {"applicant_name"}
        assert out.values["applicant_name"].value == "Asha Devi"
        assert out.validation == []


async def test_export_and_packet_hide_restricted_fields() -> None:
    async with async_session_factory() as db:
        user = await make_user(db)
        draft = restricted_draft(user)
        db.add(draft)
        await db.flush()

        text = await service.build_export(db, user, draft)
        snapshot, packet_text = await service.build_packet(db, user, draft)

        assert "Aadhaar" not in text
        assert "123456789012" not in text
        assert [field["id"] for field in snapshot["fields"]] == ["applicant_name"]
        assert "123456789012" not in packet_text
