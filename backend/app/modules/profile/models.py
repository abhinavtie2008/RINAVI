import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.modules.identity.models import utcnow


class ProfileStatus(StrEnum):
    UNCONFIRMED = "unconfirmed"
    CONFIRMED = "confirmed"
    STALE = "stale"


class ProfileValue(Base):
    __tablename__ = "profile_values"
    __table_args__ = (UniqueConstraint("user_id", "field_key"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    field_key: Mapped[str] = mapped_column(String(50), index=True)
    value: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20), default=ProfileStatus.UNCONFIRMED
    )
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    source_locator: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(10), nullable=True)
    stale_reason: Mapped[str | None] = mapped_column(String(80), nullable=True)
    correction_history: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
