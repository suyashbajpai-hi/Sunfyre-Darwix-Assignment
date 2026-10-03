"""Source-error detection and quality flags.

Checks:
* zero / implausible premium values in rate tables
* contradictory numeric facts for the same concept across documents
  (e.g. entry age "18 to 60" vs "18 to 65", hospital network 8,900 vs 9,500)
* explicitly outdated text ("THIS LINE IS OUTDATED", "superseded by")
* documents older than the newest version of the same topic
* "RATE PENDING APPROVAL" style placeholders
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, List

from ..schema import KBRecord, SourceDocument

_FACT_PATTERNS = {
    "essential_entry_age": re.compile(r"essential[^.\n]{0,80}?entry age (\d{2})\s*(?:to|-)\s*(\d{2})", re.I),
    "network_hospitals": re.compile(r"(\d[\d,]{3,6})\+?\s*network hospitals", re.I),
    "claim_tat_days": re.compile(r"average of (\d+) working days", re.I),
    "members": re.compile(r"(\d\.\d) million members", re.I),
}


def flag_documents(docs: List[SourceDocument]) -> None:
    for d in docs:
        text = "\n".join(s.text for s in d.sections)
        if re.search(r"superseded by|retained for reference|OUTDATED", text, re.I):
            d.flags.append("contains_outdated_text")
        if re.search(r"2023", d.file) or (d.doc_date and d.doc_date < "2024-01-01"):
            d.flags.append("older_edition")
            d.superseded = True


def flag_records(records: List[KBRecord]) -> Dict[str, List[str]]:
    """Returns {flag: [record_ids]} and annotates records."""
    report: Dict[str, List[str]] = defaultdict(list)
    facts: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))

    for r in records:
        c = r.content
        if re.search(r"premium[^.\n]*:\s*0\b|annual premium excl gst:\s*0\b", c, re.I):
            r.quality_flags.append("zero_premium_value")
            report["zero_premium_value"].append(r.record_id)
        if re.search(r"pending approval|tbd|to be confirmed", c, re.I):
            r.quality_flags.append("placeholder_value")
            report["placeholder_value"].append(r.record_id)
        if re.search(r"THIS LINE IS OUTDATED|legacy text", c, re.I):
            r.quality_flags.append("explicit_outdated_statement")
            report["explicit_outdated_statement"].append(r.record_id)
        for fact, pat in _FACT_PATTERNS.items():
            for m in pat.finditer(c):
                val = "-".join(g for g in m.groups() if g)
                facts[fact][val].append(r.record_id)

    for fact, by_val in facts.items():
        if len(by_val) > 1:
            desc = "; ".join(f"{v} in {', '.join(ids[:3])}" for v, ids in by_val.items())
            report[f"conflict:{fact}"].append(desc)
            for ids in by_val.values():
                for rid in ids:
                    rec = next(x for x in records if x.record_id == rid)
                    if f"conflicting_fact:{fact}" not in rec.quality_flags:
                        rec.quality_flags.append(f"conflicting_fact:{fact}")
    return dict(report)
