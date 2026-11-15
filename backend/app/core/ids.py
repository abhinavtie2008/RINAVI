import uuid
from collections.abc import Iterable


def parse_uuid(value: object) -> uuid.UUID | None:
    """Return ``value`` as a UUID, or None when it is not a valid UUID string."""
    try:
        return uuid.UUID(str(value))
    except (AttributeError, TypeError, ValueError):
        return None


def parse_uuids(values: Iterable[object]) -> list[uuid.UUID]:
    """Parse stored identifiers, skipping values that are not UUIDs.

    ``document_links`` and locker packet snapshots are JSON columns, so a
    malformed or hand-edited value must not break every later read of the
    record. A skipped id is treated as a document that is no longer available,
    which the validator already reports as ``document_unavailable``.
    """
    parsed: list[uuid.UUID] = []
    for value in values:
        parsed_id = parse_uuid(value)
        if parsed_id is not None:
            parsed.append(parsed_id)
    return parsed
