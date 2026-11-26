import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from app.modules.consent.purposes import CONSENT_PURPOSES

_ACCEPTED_PURPOSES = ", ".join(CONSENT_PURPOSES)


class ConsentGrantRequest(BaseModel):
    purpose: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
    ]

    @field_validator("purpose")
    @classmethod
    def _must_be_a_documented_purpose(cls, value: str) -> str:
        # Only the four purposes in docs/compliance/data-map.md §4 may be
        # granted. Anything else would be a row the reviewer's data map does
        # not describe, so refuse it here rather than store it.
        if value not in CONSENT_PURPOSES:
            raise ValueError(
                f"Unknown consent purpose. Accepted values: {_ACCEPTED_PURPOSES}"
            )
        return value


class ConsentRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    purpose: str
    policy_version: str
    granted_at: datetime
    withdrawn_at: datetime | None
