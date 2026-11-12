from typing import Any

from pydantic import BaseModel


class CatalogSourceOut(BaseModel):
    title: str
    url: str


class ServiceSummaryOut(BaseModel):
    slug: str
    name: str
    geography: str
    department: str
    latest_version: str
    summary: str
    fee: str
    processing_time: str


class CatalogFieldOut(BaseModel):
    id: str
    label: str
    binding: str | None
    required: bool
    format: str


class ChecklistGroupOut(BaseModel):
    id: str
    label: str
    requirement: str
    accepted_classifications: list[str]


class ServiceDetailOut(ServiceSummaryOut):
    tags: list[str]
    sources: list[CatalogSourceOut]
    guidance: dict[str, Any]
    checklist_groups: list[ChecklistGroupOut]
    fields: list[CatalogFieldOut]
    declaration: dict[str, Any]
