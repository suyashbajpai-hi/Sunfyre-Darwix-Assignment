"""PII detection and masking.

Rule-based detectors (no external service) covering the PII types that appear
in insurance/finance content: emails, phone numbers (IN/PH/ID/intl formats),
policy / account numbers, national IDs (Aadhaar, PAN, PhilSys, NIK), credit
card numbers (Luhn-checked), dates of birth and labelled person names.

`mask_text` replaces matches with typed placeholders like `[EMAIL]` so the text
stays readable for retrieval while leaking nothing. `detect` returns the
findings so a record can be flagged `pii=true` with a list of PII types.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple

_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("NIK", re.compile(r"\bNIK[:\s]*\d{16}\b", re.I)),
    ("CARD", re.compile(r"\b(?:\d[ -]?){13,19}\b")),
    ("AADHAAR", re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")),
    ("PAN", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")),
    ("PHILSYS", re.compile(r"\b\d{4}-\d{4}-\d{4}-\d{4}\b")),
    ("POLICY_NO", re.compile(r"\b(?:POL|PLCY|POLICY|ACC|ACCT|LOAN|CONTRACT|KONTRAK)(?:\s*(?:NO|NUMBER))?[-\s#:]*(?=[A-Z0-9-]*\d)[A-Z0-9][A-Z0-9-]{5,}\b", re.I)),
    ("PHONE", re.compile(r"(?<![\d,.])\+?\d[\d\s()-]{7,16}\d(?!\d)")),
    ("DOB", re.compile(r"\b(?:DOB|Date of Birth|Birth Date)[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.I)),
    ("NAME", re.compile(r"\b(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Bapak|Ibu|Ginoong|Ginang)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}")),
]


def _luhn_ok(digits: str) -> bool:
    d = [int(c) for c in digits if c.isdigit()]
    if len(d) < 13:
        return False
    checksum = 0
    parity = len(d) % 2
    for i, n in enumerate(d):
        if i % 2 == parity:
            n *= 2
            if n > 9:
                n -= 9
        checksum += n
    return checksum % 10 == 0


@dataclass
class PIIFinding:
    kind: str
    value: str
    start: int
    end: int


def detect(text: str) -> List[PIIFinding]:
    findings: List[PIIFinding] = []
    taken: List[Tuple[int, int]] = []
    for kind, pat in _PATTERNS:
        for m in pat.finditer(text):
            s, e = m.span()
            if any(not (e <= ts or s >= te) for ts, te in taken):
                continue
            val = m.group(0)
            if kind == "CARD" and not _luhn_ok(val):
                continue
            if kind == "PHONE":
                digits = re.sub(r"\D", "", val)
                # skip amounts / years / short numbers; require phone-like length
                if not (9 <= len(digits) <= 13):
                    continue
                # dates like 2024-01-15 or 15-01-2024 are not phones
                if re.fullmatch(r"\d{4}-\d{2}-\d{2}|\d{2}-\d{2}-\d{4}", val.strip()):
                    continue
            findings.append(PIIFinding(kind, val, s, e))
            taken.append((s, e))
    findings.sort(key=lambda f: f.start)
    return findings


def mask_text(text: str) -> Tuple[str, List[str]]:
    """Return (masked_text, sorted unique PII kinds found)."""
    findings = detect(text)
    if not findings:
        return text, []
    out = []
    last = 0
    for f in findings:
        out.append(text[last : f.start])
        out.append(f"[{f.kind}]")
        last = f.end
    out.append(text[last:])
    return "".join(out), sorted({f.kind for f in findings})
