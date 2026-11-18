import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DraftValueOut(BaseModel):
    value: str
    origin: str


class ValidationIssueOut(BaseModel):
    code: str
    field_id: str | None
    group_id: str | None
    document_id: str | None
    message: str


class DraftOut(BaseModel):
    id: uuid.UUID
    service_slug: str
    service_name: str
    pack_version: str
    template_snapshot: dict[str, Any]
    values: dict[str, DraftValueOut]
    document_links: dict[str, list[str]]
    declaration_confirmed: bool
    validation: list[ValidationIssueOut]
    created_at: datetime
    updated_at: datetime


class DraftCreateIn(BaseModel):
    service_slug: str = Field(max_length=80)


class FieldUpdateIn(BaseModel):
    value: str = Field(max_length=500)


class DocumentLinkIn(BaseModel):
    group_id: str = Field(max_length=80)


class DeclarationIn(BaseModel):
    confirmed: bool


class ExportOut(BaseModel):
    text: str
