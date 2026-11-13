import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Date, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.modules.identity.models import utcnow


class CaseStatus(StrEnum):
    PREPARED = "prepared"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    OUTCOME_RECEIVED = "outcome_received"
    ABANDONED = "abandoned"
    UNCERTAIN = "uncertain"


class ApplicationCase(Base):
    __tablename__ = "application_cases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    draft_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("application_drafts.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    service_slug: Mapped[str] = mapped_column(String(80))
    service_name: Mapped[str] = mapped_column(String(200))
    pack_version: Mapped[str] = mapped_column(String(20))
    packet_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    packet_text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default=CaseStatus.PREPARED)
    reference_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    acknowledgement_number: Mapped[str | None] = mapped_column(
        String(120), nullable=True
    )
    deadline_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    outcome_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )


class CaseEvent(Base):
    __tablename__ = "case_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("application_cases.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(30))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
