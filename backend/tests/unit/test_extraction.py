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


def test_income_with_paise_keeps_rupees_only() -> None:
    # Stripping every non-digit turned "120,000.00" into twelve million rupees.
    candidates = extract_candidates("Annual Income: Rs 120,000.00\n")

    assert [(c.value, c.confidence) for c in candidates] == [("120000", "high")]


def test_income_with_indian_grouping_keeps_rupees_only() -> None:
    candidates = extract_candidates("Annual Income: Rs. 1,20,000.75\n")

    assert [(c.value, c.confidence) for c in candidates] == [("120000", "high")]


def test_income_with_a_scale_word_stays_raw_and_low_confidence() -> None:
    # A lakh amount must never pass as a bare rupee figure.
    candidates = extract_candidates("Annual Income: Rs. 1.20 lakh\n")

    assert [(c.value, c.confidence) for c in candidates] == [("Rs. 1.20 lakh", "low")]


def test_negative_income_stays_raw_and_low_confidence() -> None:
    # Accounting negatives must never become a positive high-confidence income.
    for raw in ("(5,000)", "-5000"):
        candidates = extract_candidates(f"Annual Income: {raw}\n")

        assert [(c.value, c.confidence) for c in candidates] == [(raw, "low")], raw


def test_prefix_negative_income_stays_raw_and_low_confidence() -> None:
    # Currency prefixes and trailing text must not hide an accounting negative.
    for raw in ("Rs -5,000", "INR -5000", "Rs. (5,000)", "(5,000) approx"):
        candidates = extract_candidates(f"Annual Income: {raw}\n")

        assert [(c.value, c.confidence) for c in candidates] == [(raw, "low")], raw


def test_income_range_is_not_a_negative() -> None:
    # The dash between two figures separates a range, not a negative sign.
    candidates = extract_candidates("Annual Income: Rs 5,000-7,000\n")

    assert [(c.value, c.confidence) for c in candidates] == [("5000", "high")]


def test_currency_prefixed_positive_income_still_normalises() -> None:
    candidates = extract_candidates("Annual Income: INR 5,000\n")

    assert [(c.value, c.confidence) for c in candidates] == [("5000", "high")]


def test_impossible_calendar_dates_are_low_confidence() -> None:
    for raw in ("31/02/2000", "2023-02-30", "12/13/2024", "00/01/2000", "2000-00-10"):
        candidates = extract_candidates(f"Date of Birth: {raw}\n")

        assert [(c.value, c.confidence) for c in candidates] == [(raw, "low")], raw


def test_address_only_document_is_residence() -> None:
    # Delhi's residence-proof checklist group needs a classification to point
    # at; without one, an address-only document fell through to unsupported.
    candidates = extract_candidates("Address: 14, Nehru Colony, Example Nagar\n")

    assert classify(candidates) == "residence"


def test_valid_dates_stay_high_confidence() -> None:
    for raw, expected in (
        ("29/02/2024", "2024-02-29"),
        ("1994-03-12", "1994-03-12"),
        ("31/12/1999", "1999-12-31"),
    ):
        candidates = extract_candidates(f"Date of Birth: {raw}\n")

        assert [(c.value, c.confidence) for c in candidates] == [(expected, "high")], raw
