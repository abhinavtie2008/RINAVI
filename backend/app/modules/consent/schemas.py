import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class ConsentGrantRequest(BaseModel):
    purpose: Annotated[str, StringConstraints(max_length=80)]


class ConsentRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    purpose: str
    policy_version: str
    granted_at: datetime
    withdrawn_at: datetime | None
