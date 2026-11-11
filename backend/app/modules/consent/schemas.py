import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConsentGrantRequest(BaseModel):
    purpose: str


class ConsentRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    purpose: str
    policy_version: str
    granted_at: datetime
    withdrawn_at: datetime | None
