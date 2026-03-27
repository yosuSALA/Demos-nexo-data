import re
from datetime import datetime

DATE_FORMATS = (
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y-%m-%d",
    "%Y%m%d",
    "%d/%m/%y",
)

EC_NUMBER_RE = re.compile(r"^-?[\d\.]+,\d+$|^-?[\d\.]+$")


def parse_ec_number(value: str) -> float | None:
    """Parse Ecuador-format numbers like '1.188.854,66' → 1188854.66"""
    if value is None:
        return None
    value = value.strip()
    if not EC_NUMBER_RE.match(value):
        return None
    cleaned = value.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_date(raw: str) -> str | None:
    """Convert various date strings to ISO 8601 (YYYY-MM-DD)."""
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return None
