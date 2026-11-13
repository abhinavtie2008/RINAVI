import re

REDACTED = "[REDACTED]"

# Emails are matched with a linear scan instead of one regex: a single
# `local@domain` pattern backtracks quadratically on long unmatched runs.
_LOCAL_SET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._%+-"
_DOMAIN_PATTERN = re.compile(
    r"[A-Za-z0-9-]++(?:\.[A-Za-z0-9-]++)*\.[A-Za-z]{2,}"
)
DIGITS_12_PATTERN = re.compile(r"\d{12}")
DIGITS_10_PATTERN = re.compile(r"\d{10}")


def _redact_emails(value: str) -> str:
    parts = value.split("@")
    if len(parts) == 1:
        return value
    out: list[str] = []
    pending = parts[0]
    for right in parts[1:]:
        local_len = len(pending) - len(pending.rstrip(_LOCAL_SET))
        if local_len:
            match = _DOMAIN_PATTERN.match(right)
            if match is not None:
                out.append(pending[:-local_len])
                out.append(REDACTED)
                pending = right[match.end() :]
                continue
        out.append(pending)
        out.append("@")
        pending = right
    out.append(pending)
    return "".join(out)


def redact_text(value: str) -> str:
    value = _redact_emails(value)
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
