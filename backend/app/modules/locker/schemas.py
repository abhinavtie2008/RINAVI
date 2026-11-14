import uuid
from datetime import date, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from app.modules.applications.schemas import DraftOut


class CaseEventOut(BaseModel):
    id: uuid.UUID
    type: str
    payload: dict[str, Any]
    created_at: datetime


class CaseSummaryOut(BaseModel):
    id: uuid.UUID
    service_slug: str
    service_name: str
    status: str
    reference_number: str | None
    created_at: datetime


class CaseOut(CaseSummaryOut):
    draft_id: uuid.UUID | None
    pack_version: str
    acknowledgement_number: str | None
    deadline_at: date | None
    outcome_notes: str | None
    updated_at: datetime
    events: list[CaseEventOut]
    packet_snapshot: dict[str, Any]


class SubmittedEventIn(BaseModel):
    type: Literal["submitted"]
    reference_number: str | None = None


class AcknowledgedEventIn(BaseModel):
    type: Literal["acknowledged"]
    acknowledgement_number: str | None = None


class OutcomeReceivedEventIn(BaseModel):
    type: Literal["outcome_received"]
    outcome_notes: str | None = Field(default=None, max_length=2000)


class AbandonedEventIn(BaseModel):
    type: Literal["abandoned"]


class UncertainEventIn(BaseModel):
    type: Literal["uncertain"]


class DeadlineUpdatedEventIn(BaseModel):
    type: Literal["deadline_updated"]
    deadline_at: date | None = None


CaseEventIn = Annotated[
    SubmittedEventIn
    | AcknowledgedEventIn
    | OutcomeReceivedEventIn
    | AbandonedEventIn
    | UncertainEventIn
    | DeadlineUpdatedEventIn,
    Field(discriminator="type"),
]


class SuggestionOut(BaseModel):
    document_id: str
    group_id: str


class ApplyAgainOut(BaseModel):
    draft: DraftOut
    suggested_links: list[SuggestionOut]
