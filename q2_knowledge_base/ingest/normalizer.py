"""Standardisation of headings, dates, terminology, categories and form fields.

Terminology: the raw sources use "co-pay", "copayment", "co-payment",
"cash-less hospitalization", "cashless hospitalisation", "lac"/"lakh", "upto",
"PED"/"pre existing disease" interchangeably. We map everything to one canonical
form so BM25 matches and so the voice agent speaks consistently. The canonical
term list is exported as GLOSSARY for use in ASR vocabulary prompts too.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

# (regex, canonical) - order matters, longer patterns first
TERMINOLOGY: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bcash[\s-]?less hospitali[sz]ation\b", re.I), "cashless hospitalisation"),
    (re.compile(r"\bhospitalization\b", re.I), "hospitalisation"),
    (re.compile(r"\bhospitalized\b", re.I), "hospitalised"),
    (re.compile(r"\bco[\s-]?pay(?:ment)?s?\b", re.I), "co-payment"),
    (re.compile(r"\bcopayment\b", re.I), "co-payment"),
    (re.compile(r"\bpre[\s-]?existing (?:disease|condition)s?\b", re.I), "pre-existing disease"),
    (re.compile(r"\bPEDs?\b"), "pre-existing disease"),
    (re.compile(r"\bno[\s-]?claim bonus\b", re.I), "no-claim bonus"),
    (re.compile(r"\bupto\b", re.I), "up to"),
    (re.compile(r"\blife[\s-]?time renewab", re.I), "lifetime renewab"),
    (re.compile(r"\bhealth check[\s-]?ups?\b", re.I), "health check-up"),
    (re.compile(r"\bsum assured\b", re.I), "sum insured"),
    (re.compile(r"\bRs\.?\s?(\d[\d,.]*)\s?(?:lacs?|lakhs?|L)\b", re.I), r"Rs \1 lakh"),
    (re.compile(r"\b(\d[\d,.]*)\s?lacs?\b", re.I), r"\1 lakh"),
    (re.compile(r"\b(\d+)\s?%"), r"\1%"),
    (re.compile(r"\byrs?\b", re.I), "years"),
    (re.compile(r"\bu/s\s+80D\b", re.I), "under Section 80D"),
    (re.compile(r"\bTAT\b"), "turnaround time"),
    (re.compile(r"\bPPME\b"), "pre-policy medical examination"),
]

GLOSSARY = [
    "cashless hospitalisation", "co-payment", "pre-existing disease", "no-claim bonus", "sum insured", "waiting period",
    "restoration benefit", "room rent", "lifetime renewability", "free-look period", "grace period", "portability",
    "Sentinel Essential", "Sentinel Family Shield", "Sentinel Senior Care", "Critical Illness Rider", "Hospital Cash",
    "IRDAI", "Section 80D", "GST", "underwriting", "lakh",
]

_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}

_DATE_DMY = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
_DATE_DMON = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?[\s-]([A-Za-z]{3,9}),?[\s-](\d{4})\b")
_DATE_MOND = re.compile(r"\b([A-Z][a-z]{2,8})\s+(\d{1,2}),\s+(\d{4})\b")


def _mon(s: str) -> int | None:
    return _MONTHS.get(s[:3].lower())


def normalize_dates(text: str) -> str:
    """Rewrite common date formats to ISO-8601 (YYYY-MM-DD). DD/MM/YYYY assumed (India)."""

    def dmy(m):
        d, mo, y = int(m.group(1)), int(m.group(2)), m.group(3)
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y}-{mo:02d}-{d:02d}"
        return m.group(0)

    def dmon(m):
        mo = _mon(m.group(2))
        if mo is None:
            return m.group(0)
        return f"{m.group(3)}-{mo:02d}-{int(m.group(1)):02d}"

    def mond(m):
        mo = _mon(m.group(1))
        if mo is None:
            return m.group(0)
        return f"{m.group(3)}-{mo:02d}-{int(m.group(2)):02d}"

    text = _DATE_DMY.sub(dmy, text)
    text = _DATE_MOND.sub(mond, text)
    text = _DATE_DMON.sub(dmon, text)
    return text


def normalize_terminology(text: str) -> str:
    for pat, rep in TERMINOLOGY:
        text = pat.sub(rep, text)
    # Capitalise plan names consistently
    text = re.sub(r"\bSENTINEL (ESSENTIAL|FAMILY SHIELD|SENIOR CARE)\b", lambda m: "Sentinel " + m.group(1).title(), text)
    return text


def normalize_whitespace(text: str) -> str:
    text = text.replace("\u00a0", " ").replace("\u2019", "'").replace("\u2013", "-").replace("\u2014", "-")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def normalize_text(text: str) -> str:
    return normalize_terminology(normalize_dates(normalize_whitespace(text)))


_HEADING_NUM = re.compile(r"^(?:section\s+)?(?:[A-Z]|\d+)(?:\.\d+)*[.)\s-]+\s*", re.I)


def standardize_heading(h: str) -> str:
    """'## 3. Pre-existing disease (PED) acceptance grid' -> 'Pre-Existing Disease (PED) Acceptance Grid'."""
    h = normalize_whitespace(h)
    h = re.sub(r"^SECTION\s+[A-Z]\s*-\s*", "", h, flags=re.I)
    h = _HEADING_NUM.sub("", h) if re.match(r"^(?:[A-Z]|\d+)(?:\.\d+)*[.)\s-]", h) else h
    h = h.strip(" :-")
    if h.isupper():
        h = h.title()
    else:
        h = " ".join(w if (w.isupper() and len(w) <= 5) else w[:1].upper() + w[1:] for w in h.split(" "))
    return h


FIELD_SYNONYMS: Dict[str, str] = {
    "dob": "date_of_birth", "dateofbirth": "date_of_birth", "date_of_birth": "date_of_birth",
    "fullname": "full_name", "name": "full_name", "member_name": "member_name",
    "mobile_no": "mobile_number", "mobile": "mobile_number", "phone": "mobile_number",
    "emailid": "email", "email": "email", "pincode": "pin_code", "pin": "pin_code",
    "policyterm": "policy_term", "sum_insured": "sum_insured", "sum_insured_rs": "sum_insured",
    "annual_premium_rs_excl_gst": "annual_premium_excl_gst",
}


def standardize_field_name(name: str) -> str:
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower().replace("-", "_").replace(" ", "_")
    snake = re.sub(r"_+", "_", snake)
    return FIELD_SYNONYMS.get(snake.replace("_", ""), FIELD_SYNONYMS.get(snake, snake))
