import pytest
from pydantic import ValidationError

from app.modules.consent.schemas import ConsentGrantRequest
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
