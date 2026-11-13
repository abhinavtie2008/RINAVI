import re
from typing import Any

_FORMAT_PATTERNS = {
    "text": re.compile(r".+", re.DOTALL),
    "numeric": re.compile(r"\d+"),
    "date": re.compile(r"\d{4}-\d{2}-\d{2}"),
    "aadhaar": re.compile(r"\d{12}"),
}


def _issue(
    code: str,
    message: str,
    *,
    field_id: str | None = None,
    group_id: str | None = None,
    document_id: str | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "field_id": field_id,
        "group_id": group_id,
        "document_id": document_id,
        "message": message,
    }


def validate_draft(
    snapshot: dict[str, Any],
    values: dict[str, Any],
    declaration_confirmed: bool,
    document_links: dict[str, Any],
    document_states: dict[str, str],
    profile_confirmed: dict[str, str],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for field in snapshot["fields"]:
        entry = values.get(field["id"])
        if entry is None or entry["value"].strip() == "":
            if field["required"]:
                issues.append(
                    _issue(
                        "field_required",
                        "This field is required.",
                        field_id=field["id"],
                    )
                )
            continue
        if not _FORMAT_PATTERNS[field["format"]].fullmatch(entry["value"].strip()):
            issues.append(
                _issue(
                    "field_format_invalid",
                    f"Enter a valid {field['format']} value.",
                    field_id=field["id"],
                )
            )
            continue
        binding = field["binding"]
        if binding is None:
            continue
        if entry["origin"] == "citizen" and binding in profile_confirmed:
            issues.append(
                _issue(
                    "value_not_source_linked",
                    "This value comes from your profile. Correct it there, then refresh the draft.",
                    field_id=field["id"],
                )
            )
        elif entry["origin"] == "profile" and entry["value"] != profile_confirmed.get(
            binding
        ):
            issues.append(
                _issue(
                    "value_diverges_from_profile",
                    "This value no longer matches your profile. Refresh the draft.",
                    field_id=field["id"],
                )
            )
    if not declaration_confirmed:
        issues.append(
            _issue(
                "declaration_missing", "Confirm the declaration to finish the draft."
            )
        )
    for group in snapshot["checklist_groups"]:
        if group["requirement"] != "at_least_one":
            continue
        linked = document_links.get(group["id"], [])
        if not linked:
            issues.append(
                _issue(
                    "checklist_requirement_unmet",
                    f"Attach at least one document to {group['label']}.",
                    group_id=group["id"],
                )
            )
            continue
        for doc_id in linked:
            if document_states.get(doc_id) == "unavailable":
                issues.append(
                    _issue(
                        "document_unavailable",
                        "An attached document is missing or no longer processed. "
                        "Attach a different one.",
                        group_id=group["id"],
                        document_id=doc_id,
                    )
                )
    return issues
