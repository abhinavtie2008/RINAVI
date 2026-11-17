import pytest
from pydantic import ValidationError

from app.modules.applications.schemas import (
    DocumentLinkIn,
    DraftCreateIn,
    FieldUpdateIn,
)
from app.modules.consent.schemas import ConsentGrantRequest
from app.modules.identity.schemas import PasskeyFinishRequest
from app.modules.locker.schemas import AcknowledgedEventIn, SubmittedEventIn


def test_consent_purpose_over_80_chars_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ConsentGrantRequest(purpose="x" * 81)


def test_reference_number_over_120_chars_is_rejected() -> None:
    with pytest.raises(ValidationError):
        SubmittedEventIn(type="submitted", reference_number="x" * 121)


def test_acknowledgement_number_over_120_chars_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AcknowledgedEventIn(type="acknowledged", acknowledgement_number="x" * 121)


def test_draft_service_slug_over_80_chars_is_rejected() -> None:
    with pytest.raises(ValidationError):
        DraftCreateIn(service_slug="x" * 81)


def test_field_value_over_500_chars_is_rejected() -> None:
    with pytest.raises(ValidationError):
        FieldUpdateIn(value="x" * 501)


def test_document_group_id_over_80_chars_is_rejected() -> None:
    with pytest.raises(ValidationError):
        DocumentLinkIn(group_id="x" * 81)


def test_passkey_challenge_id_over_128_chars_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PasskeyFinishRequest(challenge_id="x" * 129, credential="x")


def test_passkey_credential_over_16_kib_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PasskeyFinishRequest(challenge_id="x", credential="x" * (16 * 1024 + 1))


def test_boundary_lengths_are_accepted() -> None:
    assert DraftCreateIn(service_slug="x" * 80).service_slug == "x" * 80
    assert FieldUpdateIn(value="x" * 500).value == "x" * 500
    assert DocumentLinkIn(group_id="x" * 80).group_id == "x" * 80
    request = PasskeyFinishRequest(challenge_id="x" * 128, credential="x")
    assert request.challenge_id == "x" * 128
    request = PasskeyFinishRequest(challenge_id="x", credential="x" * (16 * 1024))
    assert len(request.credential) == 16 * 1024
