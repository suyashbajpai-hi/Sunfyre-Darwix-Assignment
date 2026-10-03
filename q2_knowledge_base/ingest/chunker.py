"""Heading-aware chunking.

Strategy
--------
* One section (heading + its paragraphs / list / table) is the natural unit. A
  voice agent needs *answer-sized* chunks (one fact cluster) rather than
  fixed 512-token windows that split a table row from its header.
* Sections longer than `max_words` are split on sentence boundaries into
  windows of roughly `target_words`, with a one-sentence overlap so a fact that
  straddles the boundary is retrievable from both sides.
* FAQ sections keep question + answer together (never split).
* Table sections are split by rows, keeping the heading on every chunk so the
  plan name travels with the row.
* Every chunk title is the heading path joined with " > " so citations read like
  "Plans > Sentinel Family Shield".
"""
from __future__ import annotations

import re
from typing import List

from ..schema import KBRecord, Section, SourceDocument, SourceRef

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


def _sentences(text: str) -> List[str]:
    out = []
    for para in text.split("\n"):
        para = para.strip()
        if not para:
            continue
        if para.startswith("- ") or para.startswith("(row"):
            out.append(para)
            continue
        out.extend(s.strip() for s in _SENT_SPLIT.split(para) if s.strip())
    return out


def _windows(units: List[str], target_words: int, max_words: int) -> List[str]:
    chunks: List[str] = []
    cur: List[str] = []
    cur_words = 0
    for u in units:
        w = len(u.split())
        if cur and cur_words + w > target_words:
            chunks.append("\n".join(cur) if any(x.startswith("- ") or x.startswith("(row") for x in cur) else " ".join(cur))
            # overlap: carry last unit forward
            cur = [cur[-1]] if len(cur[-1].split()) < max_words // 3 else []
            cur_words = sum(len(x.split()) for x in cur)
        cur.append(u)
        cur_words += w
    if cur:
        chunks.append("\n".join(cur) if any(x.startswith("- ") or x.startswith("(row") for x in cur) else " ".join(cur))
    return chunks


def chunk_document(doc: SourceDocument, target_words: int = 140, max_words: int = 220) -> List[KBRecord]:
    records: List[KBRecord] = []
    idx = 0
    for sec in doc.sections:
        title_path = [doc.title] + [h for h in sec.heading_path if h and h != doc.title]
        title = " > ".join(title_path)
        words = len(sec.text.split())
        if sec.kind == "faq" or words <= max_words:
            pieces = [sec.text]
        elif sec.kind in {"table", "form"}:
            pieces = _windows(sec.text.split("\n"), target_words, max_words)
        else:
            pieces = _windows(_sentences(sec.text), target_words, max_words)

        for p in pieces:
            if len(p.split()) < 4:
                continue
            rec = KBRecord(
                record_id="",  # assigned after classification
                title=title,
                content=p.strip(),
                category="",
                source=SourceRef(file=doc.file, type=doc.source_type, locator=sec.locator, doc_version=doc.doc_version,
                                 doc_date=doc.doc_date),
                market=doc.market,
                language=doc.language,
                version="1.0",
                chunk_index=idx,
                parent_doc_id=doc.doc_id,
                superseded=doc.superseded,
                quality_flags=list(doc.flags),
                token_estimate=int(len(p.split()) * 1.3),
            )
            if sec.kind == "faq":
                rec.tags.append("faq")
            if sec.kind == "table":
                rec.tags.append("table")
            if sec.kind == "form":
                rec.tags.append("form")
            records.append(rec)
            idx += 1
    return records
