import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

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
    challenge_id: str
    credential: str
