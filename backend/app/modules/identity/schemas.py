import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.consent.schemas import ConsentRecordOut


class DevSigninRequest(BaseModel):
    email: EmailStr


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str
    created_at: datetime


class AccountExport(BaseModel):
    user: UserOut
    consent_records: list[ConsentRecordOut]


class PasskeyFinishRequest(BaseModel):
    # The challenge is a 32-character urlsafe token; the credential is a
    # base64url-encoded WebAuthn response (a few KiB at most).
    challenge_id: str = Field(max_length=128)
    credential: str = Field(max_length=16 * 1024)
