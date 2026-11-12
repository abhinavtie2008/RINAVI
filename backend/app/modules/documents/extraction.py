import re
from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader

CONFIDENCE_HIGH = "high"
CONFIDENCE_LOW = "low"

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


@dataclass(frozen=True)
class Candidate:
    field_key: str
    value: str
    confidence: str
    locator: str


def _normalize_date(raw: str) -> tuple[str, str]:
    value = raw.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value, CONFIDENCE_HIGH
    match = re.fullmatch(r"(\d{2})[/-](\d{2})[/-](\d{4})", value)
    if match:
        day, month, year = match.groups()
        return f"{year}-{month}-{day}", CONFIDENCE_HIGH
    return value, CONFIDENCE_LOW


def _normalize_gender(raw: str) -> tuple[str, str]:
    value = raw.strip().lower()
    if value in {"male", "female", "other"}:
        return value, CONFIDENCE_HIGH
    return raw.strip(), CONFIDENCE_LOW


def _normalize_income(raw: str) -> tuple[str, str]:
    digits = re.sub(r"\D", "", raw)
    if digits:
        return str(int(digits)), CONFIDENCE_HIGH
    return raw.strip(), CONFIDENCE_LOW


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
    return "unsupported"


def extract_text_from_txt(data: bytes) -> str:
    return data.decode("utf-8")


def extract_text_from_pdf(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    # Layout mode keeps line structure, which the line-locator extraction relies on.
    return "\n".join(
        page.extract_text(extraction_mode="layout") or "" for page in reader.pages
    )
