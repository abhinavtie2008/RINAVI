import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.applications.models import ApplicationDraft
from app.modules.catalog import loader
from app.modules.catalog.loader import CatalogError, ServicePack
from app.modules.identity.models import User, utcnow
from app.modules.profile.models import ProfileStatus, ProfileValue
from app.modules.vault import service as vault_service
from app.modules.vault.models import Document, DocumentStatus


class DraftError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _snapshot(pack: ServicePack) -> dict[str, Any]:
    return {
        "fields": [
            {
                "id": field.id,
                "label": field.label,
                "binding": field.binding,
                "required": field.required,
                "format": field.format,
            }
            for field in pack.fields
        ],
        "declaration": pack.declaration,
        "checklist_groups": [
            {
                "id": group.id,
                "label": group.label,
                "requirement": group.requirement,
                "accepted_classifications": group.accepted_classifications,
            }
            for group in pack.checklist_groups
        ],
        "guidance": pack.guidance,
    }


async def _confirmed_profile_values(
    db: AsyncSession, user: User
) -> dict[str, str]:
    result = await db.execute(
        select(ProfileValue).where(
            ProfileValue.user_id == user.id,
            ProfileValue.status == ProfileStatus.CONFIRMED,
        )
    )
    return {value.field_key: value.value for value in result.scalars()}


async def create_draft(
    db: AsyncSession, user: User, slug: str
) -> ApplicationDraft:
    service_metadata = loader.get_service(slug)
    pack = loader.get_latest_pack(slug)
    if service_metadata is None or pack is None:
        raise CatalogError(f"Unknown service: {slug}")
    profile = await _confirmed_profile_values(db, user)
    values = {
        field.id: {"value": profile[field.binding], "origin": "profile"}
        for field in pack.fields
        if field.binding is not None and field.binding in profile
    }
    draft = ApplicationDraft(
        user_id=user.id,
        service_slug=slug,
        service_name=service_metadata.name,
        pack_version=pack.pack_version,
        template_snapshot=_snapshot(pack),
        values=values,
        document_links={},
        declaration_confirmed=False,
    )
    db.add(draft)
    await db.flush()
    return draft


async def list_drafts(db: AsyncSession, user: User) -> list[ApplicationDraft]:
    result = await db.execute(
        select(ApplicationDraft)
        .where(ApplicationDraft.user_id == user.id)
        .order_by(ApplicationDraft.created_at.desc())
    )
    return list(result.scalars())


async def get_own_draft(
    db: AsyncSession, user: User, draft_id: uuid.UUID
) -> ApplicationDraft | None:
    result = await db.execute(
        select(ApplicationDraft).where(
            ApplicationDraft.id == draft_id,
            ApplicationDraft.user_id == user.id,
        )
    )
    return result.scalar_one_or_none()


def set_field_value(draft: ApplicationDraft, field_id: str, value: str) -> None:
    field_ids = {field["id"] for field in draft.template_snapshot["fields"]}
    if field_id not in field_ids:
        raise DraftError("unknown_field", f"Unknown field: {field_id}")
    values = dict(draft.values)
    if value == "":
        values.pop(field_id, None)
    else:
        values[field_id] = {"value": value, "origin": "citizen"}
    draft.values = values
    draft.updated_at = utcnow()


async def refresh_draft(
    db: AsyncSession, user: User, draft: ApplicationDraft
) -> None:
    profile = await _confirmed_profile_values(db, user)
    values = dict(draft.values)
    for field in draft.template_snapshot["fields"]:
        binding = field["binding"]
        if binding is None or binding not in profile:
            continue
        current = values.get(field["id"])
        if current is None or current["origin"] == "profile":
            values[field["id"]] = {"value": profile[binding], "origin": "profile"}
    draft.values = values
    draft.updated_at = utcnow()


async def link_document(
    db: AsyncSession,
    user: User,
    draft: ApplicationDraft,
    document_id: uuid.UUID,
    group_id: str,
) -> None:
    groups = {
        group["id"]: group
        for group in draft.template_snapshot["checklist_groups"]
    }
    group = groups.get(group_id)
    if group is None:
        raise DraftError("unknown_group", f"Unknown checklist group: {group_id}")
    document = await vault_service.get_own_document(db, user, document_id)
    if document is None or document.status != DocumentStatus.PROCESSED:
        raise DraftError("document_not_available", "Document is not processed")
    accepted = group["accepted_classifications"]
    if accepted and (document.classification or "") not in accepted:
        raise DraftError(
            "document_not_suitable", "Document does not match this checklist group"
        )
    links = {key: list(ids) for key, ids in draft.document_links.items()}
    ids = links.setdefault(group_id, [])
    if str(document_id) not in ids:
        ids.append(str(document_id))
    draft.document_links = links
    draft.updated_at = utcnow()


def unlink_document(draft: ApplicationDraft, document_id: uuid.UUID) -> None:
    draft.document_links = {
        group_id: [doc_id for doc_id in ids if doc_id != str(document_id)]
        for group_id, ids in draft.document_links.items()
    }
    draft.updated_at = utcnow()


def set_declaration(draft: ApplicationDraft, confirmed: bool) -> None:
    draft.declaration_confirmed = confirmed
    draft.updated_at = utcnow()


async def collect_validation_inputs(
    db: AsyncSession, user: User, draft: ApplicationDraft
) -> tuple[dict[str, str], dict[str, str]]:
    profile = await _confirmed_profile_values(db, user)
    linked_ids = {
        doc_id for ids in draft.document_links.values() for doc_id in ids
    }
    states: dict[str, str] = {}
    if linked_ids:
        result = await db.execute(
            select(Document).where(
                Document.user_id == user.id,
                Document.id.in_([uuid.UUID(doc_id) for doc_id in linked_ids]),
            )
        )
        found = {str(document.id): document for document in result.scalars()}
        for doc_id in linked_ids:
            document = found.get(doc_id)
            states[doc_id] = (
                "available"
                if document is not None
                and document.status == DocumentStatus.PROCESSED
                else "unavailable"
            )
    return profile, states


async def build_export(
    db: AsyncSession, user: User, draft: ApplicationDraft
) -> str:
    linked_ids = {
        doc_id for ids in draft.document_links.values() for doc_id in ids
    }
    names: dict[str, str] = {}
    if linked_ids:
        result = await db.execute(
            select(Document).where(
                Document.user_id == user.id,
                Document.id.in_([uuid.UUID(doc_id) for doc_id in linked_ids]),
            )
        )
        names = {
            str(document.id): document.original_filename
            for document in result.scalars()
        }
    lines = [
        "RINAVI — application draft (NOT a submission)",
        f"Service: {draft.service_name} (pack {draft.pack_version})",
        f"Prepared: {draft.updated_at.isoformat()}",
        "",
        "Fields",
    ]
    for field in draft.template_snapshot["fields"]:
        entry = draft.values.get(field["id"])
        if entry is None:
            continue
        source = "profile" if entry["origin"] == "profile" else "entered by you"
        lines.append(f"- {field['label']}: {entry['value']} ({source})")
    lines.extend(["", "Evidence"])
    for group in draft.template_snapshot["checklist_groups"]:
        linked_names = [
            names.get(doc_id, str(doc_id))
            for doc_id in draft.document_links.get(group["id"], [])
        ]
        if linked_names:
            lines.append(f"- {group['label']}: {', '.join(linked_names)}")
    lines.extend(
        [
            "",
            f"Declaration: {'CONFIRMED' if draft.declaration_confirmed else 'NOT CONFIRMED'}",
            "",
            "Official channel",
        ]
    )
    lines.extend(
        f"{index}. {step}"
        for index, step in enumerate(
            draft.template_snapshot["guidance"]["official_channel_steps"], start=1
        )
    )
    lines.extend(
        ["", draft.template_snapshot["guidance"]["not_a_submission_notice"]]
    )
    return "\n".join(lines)
