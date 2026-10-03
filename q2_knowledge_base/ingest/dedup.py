"""Exact and near-duplicate removal at chunk level.

* Exact duplicates: SHA-1 of normalised text.
* Near duplicates: Jaccard similarity on 3-word shingles (>= 0.6). This catches
  the 2023 brochure paragraphs that re-state the 2024 website with slightly
  different numbers/wording.

Conflict resolution: when two chunks are near-duplicates we keep the one from
the **newer** document (doc_date / doc_version), mark the other as superseded
and record `superseded_by`. The superseded chunk is *not* indexed for retrieval
but is kept in the records file for traceability, with a quality flag so the
report can show "stale fact detected: 8,900 hospitals (2023) vs 9,500 (2024)".
"""
from __future__ import annotations

import hashlib
import re
from typing import Dict, List, Set, Tuple

from ..schema import KBRecord


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower())


def _shingles(text: str, k: int = 3) -> Set[str]:
    toks = _norm(text).split()
    if len(toks) < k:
        return {" ".join(toks)} if toks else set()
    return {" ".join(toks[i : i + k]) for i in range(len(toks) - k + 1)}


def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _unigrams(text: str) -> Set[str]:
    return {t for t in _norm(text).split() if len(t) > 2}


def similarity(a_text: str, b_text: str) -> float:
    """Near-duplicate score in [0,1].

    Shingle Jaccard catches copy-paste; unigram-set Jaccard (down-weighted) catches
    light paraphrases such as the 2023 brochure restating the 2024 web copy with
    different numbers. Length ratio guards against a short chunk being 'contained'
    in a long one.
    """
    sa, sb = _shingles(a_text), _shingles(b_text)
    ua, ub = _unigrams(a_text), _unigrams(b_text)
    la, lb = len(ua), len(ub)
    if not la or not lb or min(la, lb) / max(la, lb) < 0.5:
        return jaccard(sa, sb)
    return max(jaccard(sa, sb), 0.9 * jaccard(ua, ub))


def _recency_key(r: KBRecord) -> Tuple[str, str]:
    return (r.source.doc_date or "0000-00-00", r.source.doc_version)


def dedup_records(records: List[KBRecord], near_threshold: float = 0.55) -> Dict[str, int]:
    stats = {"exact_duplicates": 0, "near_duplicates": 0}
    seen_hash: Dict[str, KBRecord] = {}
    survivors: List[KBRecord] = []

    # exact
    for r in records:
        h = hashlib.sha1(_norm(r.content).encode()).hexdigest()
        if h in seen_hash:
            keeper = seen_hash[h]
            loser = r
            if _recency_key(r) > _recency_key(keeper):
                keeper, loser = r, keeper
                seen_hash[h] = keeper
                survivors = [x for x in survivors if x is not loser] + [keeper]
            loser.superseded = True
            loser.quality_flags.append(f"exact_duplicate_of:{keeper.record_id}")
            stats["exact_duplicates"] += 1
        else:
            seen_hash[h] = r
            survivors.append(r)

    # near (O(n^2) is fine for a KB of a few hundred chunks; use MinHash/LSH at scale)
    cands = [r for r in survivors if not any(f.startswith("exact_duplicate_of") for f in r.quality_flags)]
    for i in range(len(cands)):
        a = cands[i]
        for j in range(i + 1, len(cands)):
            b = cands[j]
            if a.market != b.market or a.parent_doc_id == b.parent_doc_id:
                continue
            sim = similarity(a.content, b.content)
            if sim >= near_threshold:
                # prefer the newer document; if one side is already superseded (older edition) it loses
                if a.superseded != b.superseded:
                    keeper, loser = (b, a) if a.superseded else (a, b)
                else:
                    keeper, loser = (a, b) if _recency_key(a) >= _recency_key(b) else (b, a)
                loser.superseded = True
                loser.quality_flags.append(f"near_duplicate_of:{keeper.record_id} (jaccard={sim:.2f})")
                stats["near_duplicates"] += 1
    return stats
