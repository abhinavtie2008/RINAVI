import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ids import parse_uuid, parse_uuids
from app.core.privacy import (
    RESTRICTED_PROFILE_FIELD_KEYS,
    is_restricted_binding,
    is_restricted_format,
)
from app.modules.applications.models import ApplicationDraft
from app.modules.applications.schemas import DraftOut, ValidationIssueOut
from app.modules.applications.validator import validate_draft
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
            if not is_restricted_binding(field.binding)
            and not is_restricted_format(field.format)
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
            ProfileValue.field_key.not_in(RESTRICTED_PROFILE_FIELD_KEYS),
        )
    )
    return {value.field_key: value.value for value in result.scalars()}


def _is_restricted_snapshot_field(field: dict[str, Any]) -> bool:
    return is_restricted_binding(field.get("binding")) or is_restricted_format(
        field.get("format")
    )


def _public_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Drop fields whose value belongs only at the official portal.

    New drafts are snapshotted without restricted bindings. Older drafts may
    still carry one, so every response path filters again.
    """
    fields = [
        field
        for field in snapshot["fields"]
        if not _is_restricted_snapshot_field(field)
    ]
    if len(fields) == len(snapshot["fields"]):
        return snapshot
    return {**snapshot, "fields": fields}


def _public_values(
    snapshot: dict[str, Any], values: dict[str, Any]
) -> dict[str, Any]:
    field_ids = {field["id"] for field in snapshot["fields"]}
    return {
        field_id: entry
        for field_id, entry in values.items()
        if field_id in field_ids
    }


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
    fields = {field["id"]: field for field in draft.template_snapshot["fields"]}
    field = fields.get(field_id)
    if field is None:
        raise DraftError("unknown_field", f"Unknown field: {field_id}")
    if _is_restricted_snapshot_field(field):
        raise DraftError(
            "restricted_field",
            f"Field is collected only at the official portal: {field_id}",
        )
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
        if (
            binding is None
            or is_restricted_binding(binding)
            or binding not in profile
        ):
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


def _linked_ids(draft: ApplicationDraft) -> set[str]:
    return {doc_id for ids in draft.document_links.values() for doc_id in ids}


async def _documents_by_id(
    db: AsyncSession, user: User, linked_ids: set[str]
) -> dict[uuid.UUID, Document]:
    stored_ids = parse_uuids(linked_ids)
    if not stored_ids:
        return {}
    result = await db.execute(
        select(Document).where(
            Document.user_id == user.id,
            Document.id.in_(stored_ids),
        )
    )
    return {document.id: document for document in result.scalars()}


def _document_states(
    draft: ApplicationDraft, found: dict[uuid.UUID, Document]
) -> dict[str, str]:
    states: dict[str, str] = {}
    for doc_id in _linked_ids(draft):
        parsed_id = parse_uuid(doc_id)
        document = found.get(parsed_id) if parsed_id is not None else None
        states[doc_id] = (
            "available"
            if document is not None and document.status == DocumentStatus.PROCESSED
            else "unavailable"
        )
    return states


async def collect_validation_inputs(
    db: AsyncSession, user: User, draft: ApplicationDraft
) -> tuple[dict[str, str], dict[str, str]]:
    profile = await _confirmed_profile_values(db, user)
    found = await _documents_by_id(db, user, _linked_ids(draft))
    return profile, _document_states(draft, found)


async def validation_issues(
    db: AsyncSession, user: User, draft: ApplicationDraft
) -> list[dict[str, Any]]:
    snapshot = _public_snapshot(draft.template_snapshot)
    values = _public_values(snapshot, draft.values)
    profile, states = await collect_validation_inputs(db, user, draft)
    return validate_draft(
        snapshot,
        values,
        draft.declaration_confirmed,
        draft.document_links,
        states,
        profile,
    )


async def build_export(
    db: AsyncSession, user: User, draft: ApplicationDraft
) -> str:
    found = await _documents_by_id(db, user, _linked_ids(draft))
    names = {
        str(document_id): document.original_filename
        for document_id, document in found.items()
    }
    lines = [
        "RINAVI — application draft (NOT a submission)",
        f"Service: {draft.service_name} (pack {draft.pack_version})",
        f"Prepared: {draft.updated_at.isoformat()}",
        "",
        "Fields",
    ]
    for field in _public_snapshot(draft.template_snapshot)["fields"]:
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


PORTAL_DOWN_GUIDANCE = (
    "If the portal is unavailable, nothing here changes. Your packet stays in "
    "the locker. Try the official channel again later — RINAVI does not submit "
    "on your behalf."
)
ACKNOWLEDGEMENT_GUIDANCE = (
    "No acknowledgement yet? Some portals send receipts later. Check your "
    "email and the portal, then record the acknowledgement number here when "
    "it arrives."
)


async def build_packet(
    db: AsyncSession, user: User, draft: ApplicationDraft
) -> tuple[dict[str, Any], str]:
    found = await _documents_by_id(db, user, _linked_ids(draft))
    names = {
        str(document_id): document.original_filename
        for document_id, document in found.items()
    }
    guidance = draft.template_snapshot["guidance"]
    service_metadata = loader.get_service(draft.service_slug)
    snapshot: dict[str, Any] = {
        "fields": [
            {
                "id": field["id"],
                "label": field["label"],
                "value": draft.values[field["id"]]["value"],
                "origin": draft.values[field["id"]]["origin"],
            }
            for field in _public_snapshot(draft.template_snapshot)["fields"]
            if field["id"] in draft.values
        ],
        "evidence": [
            {
                "group_id": group["id"],
                "group_label": group["label"],
                "documents": [
                    {"document_id": doc_id, "filename": names.get(doc_id, doc_id)}
                    for doc_id in draft.document_links.get(group["id"], [])
                ],
            }
            for group in draft.template_snapshot["checklist_groups"]
        ],
        "declaration": draft.template_snapshot["declaration"],
        "official_channel_steps": guidance["official_channel_steps"],
        "processing_time": (
            service_metadata.processing_time if service_metadata else None
        ),
        "not_a_submission_notice": guidance["not_a_submission_notice"],
        "portal_down_guidance": PORTAL_DOWN_GUIDANCE,
        "acknowledgement_guidance": ACKNOWLEDGEMENT_GUIDANCE,
    }
    return snapshot, await build_export(db, user, draft)


def _draft_out(
    draft: ApplicationDraft,
    snapshot: dict[str, Any],
    values: dict[str, Any],
    issues: list[dict[str, Any]],
) -> DraftOut:
    return DraftOut(
        id=draft.id,
        service_slug=draft.service_slug,
        service_name=draft.service_name,
        pack_version=draft.pack_version,
        template_snapshot=snapshot,
        values=values,
        document_links=draft.document_links,
        declaration_confirmed=draft.declaration_confirmed,
        validation=[ValidationIssueOut(**issue) for issue in issues],
        created_at=draft.created_at,
        updated_at=draft.updated_at,
    )


async def draft_out(
    db: AsyncSession, user: User, draft: ApplicationDraft
) -> DraftOut:
    snapshot = _public_snapshot(draft.template_snapshot)
    values = _public_values(snapshot, draft.values)
    issues = await validation_issues(db, user, draft)
    return _draft_out(draft, snapshot, values, issues)


async def drafts_out(
    db: AsyncSession, user: User, drafts: list[ApplicationDraft]
) -> list[DraftOut]:
    """Serialize many drafts with one profile read and one document read.

    Calling ``draft_out`` per row re-ran both queries for every draft.
    """
    if not drafts:
        return []
    profile = await _confirmed_profile_values(db, user)
    linked_ids = {doc_id for draft in drafts for doc_id in _linked_ids(draft)}
    found = await _documents_by_id(db, user, linked_ids)
    outputs: list[DraftOut] = []
    for draft in drafts:
        snapshot = _public_snapshot(draft.template_snapshot)
        values = _public_values(snapshot, draft.values)
        issues = validate_draft(
            snapshot,
            values,
            draft.declaration_confirmed,
            draft.document_links,
            _document_states(draft, found),
            profile,
        )
        outputs.append(_draft_out(draft, snapshot, values, issues))
    return outputs
