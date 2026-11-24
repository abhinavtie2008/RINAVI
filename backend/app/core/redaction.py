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
# Extraction accepts an Aadhaar number written in the groups printed on the
# card ("1234 5678 9012"), so the same form can reach a log through a field
# value or an exception message. Redacting only the unbroken run left it in
# clear.
# A longer run of space-separated digits ("1234 5678 9012 34") is not an
# Aadhaar number, so the pattern must not match three groups out of four.
GROUPED_12_PATTERN = re.compile(
    r"(?<!\d)(?<!\d[ -])\d{4}[ -]\d{4}[ -]\d{4}(?![ -]?\d)"
)
# Resource identifiers (case/audit IDs) are canonical UUIDs. Their final
# group can be all digits, which must not be mistaken for an Aadhaar or phone
# number: redacting it breaks correlation between API responses, audit rows,
# and logs. UUIDs carry no PII, so preserve them verbatim.
UUID_PATTERN = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
# SHA-256 digests are 64 hex characters (session rate-limit keys, token
# hashes). A 12-digit run inside one is indistinguishable from an Aadhaar
# number, so redacting it corrupts the correlation key — and made the
# "session key reaches the logs intact" assertion fail intermittently.
DIGEST_PATTERN = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])")
# Identifiers that are safe to keep verbatim: canonical UUIDs and digests.
SAFE_ID_PATTERN = re.compile(f"{UUID_PATTERN.pattern}|{DIGEST_PATTERN.pattern}")


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


def _redact_digit_runs(value: str) -> str:
    value = GROUPED_12_PATTERN.sub(REDACTED, value)
    value = DIGITS_12_PATTERN.sub(REDACTED, value)
    return DIGITS_10_PATTERN.sub(REDACTED, value)


def redact_text(value: str) -> str:
    value = _redact_emails(value)
    parts: list[str] = []
    start = 0
    for match in SAFE_ID_PATTERN.finditer(value):
        parts.append(_redact_digit_runs(value[start : match.start()]))
        parts.append(match.group(0))
        start = match.end()
    parts.append(_redact_digit_runs(value[start:]))
    return "".join(parts)


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
