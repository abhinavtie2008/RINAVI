import re

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
DIGITS_12_PATTERN = re.compile(r"\d{12}")
DIGITS_10_PATTERN = re.compile(r"\d{10}")

REDACTED = "[REDACTED]"


def redact_text(value: str) -> str:
    value = EMAIL_PATTERN.sub(REDACTED, value)
    value = DIGITS_12_PATTERN.sub(REDACTED, value)
    value = DIGITS_10_PATTERN.sub(REDACTED, value)
    return value


def redact(value: object) -> object:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, int):
        text = redact_text(str(value))
        return REDACTED if REDACTED in text else value
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    return value
