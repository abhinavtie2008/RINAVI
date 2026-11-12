import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redaction import redact
from app.modules.audit.models import AuditEvent


async def emit_audit(
    db: AsyncSession,
    *,
    actor_user_id: uuid.UUID | None,
    action: str,
    resource_type: str,
    resource_id: str,
    details: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=redact(details or {}),
    )
    db.add(event)
    await db.flush()
    return event
