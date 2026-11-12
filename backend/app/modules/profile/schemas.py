import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PromoteRequest(BaseModel):
    document_id: uuid.UUID


class CorrectRequest(BaseModel):
    value: str = Field(min_length=1, max_length=500)


class ProfileValueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    field_key: str
    value: str
    status: str
    source_document_id: uuid.UUID | None
    source_locator: str | None
    confidence: str | None
    stale_reason: str | None
    correction_history: list[dict[str, Any]]
    updated_at: datetime
