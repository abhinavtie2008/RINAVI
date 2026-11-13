from app.modules.applications.service import _snapshot
from app.modules.applications.validator import _FORMAT_PATTERNS, validate_draft
from app.modules.catalog.loader import get_latest_pack

PACK = get_latest_pack("delhi-income-certificate")
assert PACK is not None
SNAPSHOT = _snapshot(PACK)
REQUIRED_FIELD_IDS = {f["id"] for f in SNAPSHOT["fields"] if f["required"]}


def test_empty_draft_reports_required_fields_declaration_and_checklist() -> None:
    issues = validate_draft(SNAPSHOT, {}, False, {}, {}, {})
    codes = {issue["code"] for issue in issues}
    assert "field_required" in codes
    assert "declaration_missing" in codes
    assert "checklist_requirement_unmet" in codes
    required = {i["field_id"] for i in issues if i["code"] == "field_required"}
    assert required == REQUIRED_FIELD_IDS
    groups = {
        i["group_id"] for i in issues if i["code"] == "checklist_requirement_unmet"
    }
    assert groups == {
        g["id"] for g in SNAPSHOT["checklist_groups"] if g["requirement"] == "at_least_one"
    }


def test_invalid_formats_are_flagged_per_field() -> None:
    values = {
        "date_of_birth": {"value": "12/03/1994", "origin": "citizen"},
        "annual_income": {"value": "Rs. 1,20,000", "origin": "citizen"},
    }
    issues = validate_draft(SNAPSHOT, values, True, {}, {}, {})
    format_issues = [i for i in issues if i["code"] == "field_format_invalid"]
    assert {i["field_id"] for i in format_issues} == {
        "date_of_birth",
        "annual_income",
    }


def test_format_patterns_cover_vocabulary() -> None:
    assert _FORMAT_PATTERNS["numeric"].fullmatch("120000")
    assert not _FORMAT_PATTERNS["numeric"].fullmatch("1,20,000")
    assert _FORMAT_PATTERNS["date"].fullmatch("1994-03-12")
    assert not _FORMAT_PATTERNS["date"].fullmatch("12/03/1994")
    assert _FORMAT_PATTERNS["aadhaar"].fullmatch("123456789012")
    assert not _FORMAT_PATTERNS["aadhaar"].fullmatch("1234 5678 9012")
    assert _FORMAT_PATTERNS["text"].fullmatch("Scholarship application")


def test_citizen_value_on_bound_field_is_flagged() -> None:
    values = {"applicant_name": {"value": "Fake Name", "origin": "citizen"}}
    issues = validate_draft(SNAPSHOT, values, True, {}, {}, {"full_name": "Asha Devi"})
    assert any(
        i["code"] == "value_not_source_linked" and i["field_id"] == "applicant_name"
        for i in issues
    )


def test_diverged_profile_value_is_flagged() -> None:
    values = {"applicant_name": {"value": "Asha Devi", "origin": "profile"}}
    issues = validate_draft(
        SNAPSHOT, values, True, {}, {}, {"full_name": "Asha Devi Sharma"}
    )
    assert any(
        i["code"] == "value_diverges_from_profile" and i["field_id"] == "applicant_name"
        for i in issues
    )


def test_unavailable_linked_document_is_flagged() -> None:
    issues = validate_draft(
        SNAPSHOT,
        {},
        True,
        {"income_evidence": ["doc-1"]},
        {"doc-1": "unavailable"},
        {},
    )
    assert any(
        i["code"] == "document_unavailable" and i["document_id"] == "doc-1"
        for i in issues
    )


def test_valid_draft_has_no_issues() -> None:
    profile = {
        "full_name": "Asha Devi",
        "father_name": "Rajesh Devi",
        "date_of_birth": "1994-03-12",
        "gender": "female",
        "address": "14, Nehru Colony, Example Nagar",
        "annual_income": "120000",
    }
    values = {
        field["id"]: {"value": profile[field["binding"]], "origin": "profile"}
        for field in SNAPSHOT["fields"]
        if field["binding"] is not None
    }
    values["occupation"] = {"value": "Private service", "origin": "citizen"}
    values["purpose"] = {"value": "Scholarship application", "origin": "citizen"}
    issues = validate_draft(
        SNAPSHOT,
        values,
        True,
        {
            "identity_proof": ["doc-1"],
            "residence_proof": ["doc-1"],
            "income_evidence": ["doc-2"],
        },
        {"doc-1": "available", "doc-2": "available"},
        profile,
    )
    assert issues == []
