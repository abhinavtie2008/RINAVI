"""Fields RINAVI must not store or show outside the official portal."""

RESTRICTED_PROFILE_FIELD_KEYS = frozenset({"aadhaar_number"})


def is_restricted_field_key(field_key: str) -> bool:
    """Return True when a profile or extracted field must never be promoted."""
    return field_key in RESTRICTED_PROFILE_FIELD_KEYS


def is_restricted_binding(binding: str | None) -> bool:
    """Return True when a pack field binds to a portal-only identifier."""
    return binding is not None and binding in RESTRICTED_PROFILE_FIELD_KEYS
