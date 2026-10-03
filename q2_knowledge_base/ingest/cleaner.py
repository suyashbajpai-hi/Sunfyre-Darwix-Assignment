"""Cleaning: boilerplate removal, repeated-section removal, irrelevant content.

Two complementary techniques:

1. **Pattern-based** - lines that match known boilerplate (cookie notices,
   copyright, "All rights reserved", registered-office footers, promo banners).
2. **Cross-document frequency** - any normalised line that appears in 3 or more
   different source documents is treated as repeated boilerplate (site-wide
   footer text, repeated disclaimers) and removed from all but a single
   designated "company" record so the fact itself is not lost.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List

from ..schema import SourceDocument

_BOILERPLATE = [
    re.compile(r"we use cookies", re.I),
    re.compile(r"all rights reserved", re.I),
    re.compile(r"^\W*(©|copyright)\b", re.I),
    re.compile(r"^(home|plans|faq|partners|claims|customer login|accept)$", re.I),
    re.compile(r"privacy policy\s*\|", re.I),
    re.compile(r"limited period offer", re.I),
    re.compile(r"^(exported by|internal only|contains customer details)", re.I),
    re.compile(r"^-{3,}$"),
    re.compile(r"^\(?superseded by .*retained for reference\)?$", re.I),
]

_IRRELEVANT = [
    re.compile(r"\bwindow\.dataLayer\b"),
    re.compile(r"^\s*$"),
]


def _norm_line(line: str) -> str:
    return re.sub(r"\W+", " ", line.lower()).strip()


def clean_documents(docs: List[SourceDocument], repeat_threshold: int = 3) -> Dict[str, int]:
    """Mutates docs in place. Returns stats."""
    stats = Counter()
    line_docs: Dict[str, set] = {}
    for d in docs:
        if d.status != "ok":
            continue
        seen = set()
        for s in d.sections:
            for ln in s.text.splitlines():
                n = _norm_line(ln)
                if len(n) > 25 and n not in seen:
                    seen.add(n)
                    line_docs.setdefault(n, set()).add(d.doc_id)
    repeated = {n for n, ds in line_docs.items() if len(ds) >= repeat_threshold}

    kept_repeated_once = set()
    for d in docs:
        if d.status != "ok":
            continue
        new_sections = []
        for s in d.sections:
            out_lines = []
            for ln in s.text.splitlines():
                n = _norm_line(ln)
                if any(p.search(ln) for p in _BOILERPLATE):
                    stats["boilerplate_lines_removed"] += 1
                    continue
                if any(p.search(ln) for p in _IRRELEVANT):
                    stats["irrelevant_lines_removed"] += 1
                    continue
                if n in repeated:
                    if n in kept_repeated_once:
                        stats["repeated_lines_removed"] += 1
                        continue
                    kept_repeated_once.add(n)
                out_lines.append(ln)
            text = "\n".join(out_lines).strip()
            if text:
                s.text = text
                new_sections.append(s)
            else:
                stats["empty_sections_dropped"] += 1
        d.sections = new_sections
        d.clean_chars = sum(len(s.text) for s in d.sections)
    stats["repeated_patterns_detected"] = len(repeated)
    return dict(stats)
