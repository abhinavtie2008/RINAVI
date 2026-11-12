from app.modules.documents.extraction import (
    Candidate,
    classify,
    extract_candidates,
    extract_text_from_pdf,
    extract_text_from_txt,
)
from tests.factories import make_text_pdf

INCOME_TEXT = (
    "GOVERNMENT OF EXAMPLE STATE\n"
    "Income Certificate\n"
    "\n"
    "Applicant Name: Asha Devi\n"
    "Father's Name: Rajesh Devi\n"
    "Date of Birth: 12/03/1994\n"
    "Gender: Female\n"
    "Address: 14, Nehru Colony, Example Nagar\n"
    "Annual Income: Rs. 1,20,000\n"
    "Aadhaar: 1234 5678 9012\n"
)


def test_extracts_all_fields_with_high_confidence() -> None:
    candidates = extract_candidates(INCOME_TEXT)
    by_key = {c.field_key: c for c in candidates}

    assert set(by_key) == {
        "full_name",
        "father_name",
        "date_of_birth",
        "gender",
        "address",
        "annual_income",
        "aadhaar_number",
    }
    assert by_key["full_name"].value == "Asha Devi"
    assert by_key["father_name"].value == "Rajesh Devi"
    assert by_key["date_of_birth"].value == "1994-03-12"
    assert by_key["gender"].value == "female"
    assert by_key["annual_income"].value == "120000"
    assert by_key["aadhaar_number"].value == "123456789012"
    assert {c.confidence for c in candidates} == {"high"}
    assert by_key["full_name"].locator == "line 4"


def test_unnormalizable_values_are_low_confidence() -> None:
    text = (
        "Date of Birth: sometime in 1994\n"
        "Gender: Prefer not to say\n"
        "Annual Income: not available\n"
        "Aadhaar: 12345\n"
    )

    candidates = extract_candidates(text)

    assert len(candidates) == 4
    assert {c.confidence for c in candidates} == {"low"}
    by_key = {c.field_key: c for c in candidates}
    assert by_key["date_of_birth"].value == "sometime in 1994"
    assert by_key["aadhaar_number"].value == "12345"


def test_unlabeled_text_yields_no_candidates() -> None:
    assert extract_candidates("Hello world\nNothing to see here.\n") == []


def test_classification_uses_present_fields() -> None:
    income = [Candidate("annual_income", "120000", "high", "line 1")]
    identity = [Candidate("aadhaar_number", "123456789012", "high", "line 1")]
    assert classify(income) == "income"
    assert classify(identity) == "identity"
    assert classify([]) == "unsupported"


def test_pdf_text_layer_is_extracted() -> None:
    pdf_bytes = make_text_pdf(
        ["Applicant Name: Asha Devi", "Annual Income: Rs. 1,20,000"]
    )

    text = extract_text_from_pdf(pdf_bytes)

    assert "Asha Devi" in text
    fields = {c.field_key: c.value for c in extract_candidates(text)}
    assert fields.get("full_name") == "Asha Devi"
    assert fields.get("annual_income") == "120000"


def test_txt_text_is_decoded_as_utf8() -> None:
    assert extract_text_from_txt(b"Name: Asha Devi\n") == "Name: Asha Devi\n"
