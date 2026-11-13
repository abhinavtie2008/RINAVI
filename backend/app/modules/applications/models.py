import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.modules.identity.models import utcnow


class ApplicationDraft(Base):
    __tablename__ = "application_drafts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    service_slug: Mapped[str] = mapped_column(String(80))
    service_name: Mapped[str] = mapped_column(String(200))
    pack_version: Mapped[str] = mapped_column(String(20))
    template_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    values: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    document_links: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    declaration_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )
