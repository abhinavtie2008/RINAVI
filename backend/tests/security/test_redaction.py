import logging

from app.core.db import async_session_factory
from app.core.logging import RedactingFilter, configure_logging
from app.core.redaction import REDACTED, redact, redact_text
from app.modules.audit.models import AuditEvent
from app.modules.audit.service import emit_audit
from app.modules.identity import service as identity_service


def test_redact_text_scrubs_email_and_digit_runs() -> None:
    assert (
        redact_text("mail citizen@example.com now")
        == "mail [REDACTED] now"
    )
    assert redact_text("aadhaar 123456789012 end") == "aadhaar [REDACTED] end"
    assert redact_text("phone 9876543210 end") == "phone [REDACTED] end"
    assert redact_text("aadhaar id123456789012 end") == "aadhaar id[REDACTED] end"


def test_redact_recurses_into_containers() -> None:
    payload = {
        "nested": ["contact citizen@example.com", {"x": 5}],
        "keep": 5,
    }
    assert redact(payload) == {"nested": ["contact [REDACTED]", {"x": 5}], "keep": 5}


def test_redact_scrubs_numeric_scalars() -> None:
    assert redact(123456789012) == REDACTED
    assert redact(9876543210) == REDACTED
    assert redact(5) == 5


def test_redacting_filter_scrubs_message_and_args() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="user %s uploaded",
        args=("citizen@example.com",),
        exc_info=None,
    )
    assert RedactingFilter().filter(record) is True
    assert record.msg == "user [REDACTED] uploaded"
    assert record.args == ()


def test_redacting_filter_scrubs_embedded_pii_in_message() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="user citizen@example.com uploaded",
        args=None,
        exc_info=None,
    )
    assert RedactingFilter().filter(record) is True
    assert record.msg == "user [REDACTED] uploaded"


async def test_emit_audit_redacts_details() -> None:
    async with async_session_factory() as db:
        user = await identity_service.get_or_create_user(db, "citizen@example.com")
        await db.commit()

        event = await emit_audit(
            db,
            actor_user_id=user.id,
            action="document.uploaded",
            resource_type="document",
            resource_id="doc-1",
            details={"contact": "citizen@example.com", "aadhaar": 123456789012},
        )
        await db.commit()

        fetched = await db.get(AuditEvent, event.id)
        assert fetched is not None
        assert fetched.details == {"contact": "[REDACTED]", "aadhaar": "[REDACTED]"}


async def test_audit_event_survives_actor_deletion_with_null_actor() -> None:
    async with async_session_factory() as db:
        user = await identity_service.get_or_create_user(db, "citizen@example.com")
        await db.commit()

        event = await emit_audit(
            db,
            actor_user_id=user.id,
            action="account.deleted",
            resource_type="user",
            resource_id=str(user.id),
        )
        await db.commit()

        await db.delete(user)
        await db.commit()

    # Fetch in a fresh session: the deleting session's identity map still
    # caches the event with its pre-delete actor_user_id.
    async with async_session_factory() as db2:
        fetched = await db2.get(AuditEvent, event.id)
        assert fetched is not None
        assert fetched.actor_user_id is None


def test_configure_logging_applies_level() -> None:
    configure_logging("debug")
    assert logging.getLogger().level == logging.DEBUG
