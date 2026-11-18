import re
from dataclasses import dataclass
from datetime import date
from io import BytesIO

from pypdf import PdfReader

CONFIDENCE_HIGH = "high"
CONFIDENCE_LOW = "low"

# Classifications a processed document can hold. A checklist group may only
# name these: any other value matches no document at all.
CLASSIFICATIONS = ("income", "identity", "residence")
UNSUPPORTED = "unsupported"

FIELD_KEYS = (
    "full_name",
    "father_name",
    "date_of_birth",
    "gender",
    "address",
    "annual_income",
    "aadhaar_number",
)

_PATTERNS: dict[str, re.Pattern[str]] = {
    "full_name": re.compile(r"^(?:applicant\s+)?name\s*:\s*(?P<value>.+)$", re.IGNORECASE),
    "father_name": re.compile(r"^father'?s?\s+name\s*:\s*(?P<value>.+)$", re.IGNORECASE),
    "date_of_birth": re.compile(
        r"^(?:date\s+of\s+birth|dob)\s*:\s*(?P<value>.+)$", re.IGNORECASE
    ),
    "gender": re.compile(r"^gender\s*:\s*(?P<value>.+)$", re.IGNORECASE),
    "address": re.compile(r"^address\s*:\s*(?P<value>.+)$", re.IGNORECASE),
    "annual_income": re.compile(
        r"^(?:annual\s+)?income\s*:\s*(?P<value>.+)$", re.IGNORECASE
    ),
    "aadhaar_number": re.compile(
        r"^aadhaar(?:\s+number)?\s*:\s*(?P<value>.+)$", re.IGNORECASE
    ),
}

# A rupee amount: optional Indian or western grouping, optional paise.
_AMOUNT = re.compile(r"\d[\d,]*(?:\.\d+)?")
# "1.20 lakh" is not rupees; scaling it by hand is safer than guessing.
_SCALE_WORD = re.compile(r"\b(?:lakhs?|lacs?|crores?|million|billion)\b", re.IGNORECASE)
# Currency prefixes precede the figure itself; strip them to inspect it.
_CURRENCY_PREFIX = re.compile(r"^\s*(?:rs\.?|inr|₹)\s*", re.IGNORECASE)
# A parenthesised amount is a loss ("(5,000)"), possibly with trailing text.
_PAREN_AMOUNT = re.compile(r"\([\d,]+(?:\.\d+)?\)")
_ISO_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_DAY_FIRST_DATE = re.compile(r"(\d{2})[/-](\d{2})[/-](\d{4})")


@dataclass(frozen=True)
class Candidate:
    field_key: str
    value: str
    confidence: str
    locator: str


def _iso_date_or_raw(
    value: str, year: str, month: str, day: str
) -> tuple[str, str]:
    # Shapes like 2000-02-31 parse as digits but not as a real day, so the
    # calendar itself decides: an impossible date stays raw and low confidence.
    try:
        parsed = date(int(year), int(month), int(day))
    except ValueError:
        return value, CONFIDENCE_LOW
    return parsed.isoformat(), CONFIDENCE_HIGH


def _normalize_date(raw: str) -> tuple[str, str]:
    value = raw.strip()
    iso = _ISO_DATE.fullmatch(value)
    if iso is not None:
        return _iso_date_or_raw(value, *iso.groups())
    day_first = _DAY_FIRST_DATE.fullmatch(value)
    if day_first is not None:
        day, month, year = day_first.groups()
        return _iso_date_or_raw(value, year, month, day)
    return value, CONFIDENCE_LOW


def _normalize_gender(raw: str) -> tuple[str, str]:
    value = raw.strip().lower()
    if value in {"male", "female", "other"}:
        return value, CONFIDENCE_HIGH
    return raw.strip(), CONFIDENCE_LOW


def _normalize_income(raw: str) -> tuple[str, str]:
    value = raw.strip()
    if _SCALE_WORD.search(value):
        return value, CONFIDENCE_LOW
    rest = _CURRENCY_PREFIX.sub("", value, count=1).strip()
    if (
        (value.startswith("(") and value.endswith(")"))
        or rest.startswith("-")
        or _PAREN_AMOUNT.match(rest) is not None
    ):
        # Accounting negatives are losses, never income; keep them for review.
        # The range dash in "Rs 5,000-7,000" follows a digit, so it is not a sign.
        return value, CONFIDENCE_LOW
    amount = _AMOUNT.search(value)
    if amount is None:
        return value, CONFIDENCE_LOW
    # Keep rupees and drop paise: deleting every non-digit instead merged the
    # paise into the rupees ("120,000.00" became 12000000).
    rupees = amount.group().split(".", 1)[0].replace(",", "")
    return str(int(rupees)), CONFIDENCE_HIGH


def _normalize_aadhaar(raw: str) -> tuple[str, str]:
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 12:
        return digits, CONFIDENCE_HIGH
    return raw.strip(), CONFIDENCE_LOW


def _normalize_plain(raw: str) -> tuple[str, str]:
    value = raw.strip()
    if value:
        return value, CONFIDENCE_HIGH
    return value, CONFIDENCE_LOW


_NORMALIZERS = {
    "full_name": _normalize_plain,
    "father_name": _normalize_plain,
    "date_of_birth": _normalize_date,
    "gender": _normalize_gender,
    "address": _normalize_plain,
    "annual_income": _normalize_income,
    "aadhaar_number": _normalize_aadhaar,
}


def extract_candidates(text: str) -> list[Candidate]:
    candidates: list[Candidate] = []
    seen: set[str] = set()
    for line_number, line in enumerate(text.splitlines(), start=1):
        # Collapse whitespace: PDF layout mode can pad words with multiple spaces.
        stripped = " ".join(line.split())
        if not stripped:
            continue
        for field_key, pattern in _PATTERNS.items():
            if field_key in seen:
                continue
            match = pattern.match(stripped)
            if match is None:
                continue
            value, confidence = _NORMALIZERS[field_key](match.group("value"))
            candidates.append(
                Candidate(field_key, value, confidence, f"line {line_number}")
            )
            seen.add(field_key)
    return candidates


def classify(candidates: list[Candidate]) -> str:
    keys = {candidate.field_key for candidate in candidates}
    if "annual_income" in keys:
        return "income"
    if "aadhaar_number" in keys:
        return "identity"
    if "address" in keys:
        return "residence"
    return UNSUPPORTED


def extract_text_from_txt(data: bytes) -> str:
    return data.decode("utf-8")


# Bounds on how much of a PDF is read: a hostile document must not consume
# unbounded pages or memory.
PAGE_LIMIT = 100
TEXT_LIMIT_CHARS = 2 * 1024 * 1024


def extract_text_from_pdf(data: bytes) -> tuple[str, str | None]:
    """Extract text, stopping at the page or text limit.

    The returned note names the limit that stopped extraction
    (``page_limit_exceeded`` / ``text_limit_exceeded``), or is None when
    the whole document fit within both limits.
    """
    reader = PdfReader(BytesIO(data))
    parts: list[str] = []
    total = 0
    for index, page in enumerate(reader.pages):
        if index == PAGE_LIMIT:
            return "\n".join(parts), "page_limit_exceeded"
        # Layout mode keeps line structure, which the line-locator extraction
        # relies on.
        page_text = page.extract_text(extraction_mode="layout") or ""
        total += len(page_text)
        if total > TEXT_LIMIT_CHARS:
            return "\n".join(parts), "text_limit_exceeded"
        parts.append(page_text)
    return "\n".join(parts), None
