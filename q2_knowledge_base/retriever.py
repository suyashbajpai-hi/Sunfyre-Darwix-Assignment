"""Hybrid retrieval with grounding confidence and citations.

Ranking logic
-------------
1. Query normalisation: same terminology map as the corpus ("copay" -> "co-payment")
   plus a small synonym expansion ("price" -> "premium", "kids" -> "children").
2. Sparse: BM25 over all active records (filtered by market / category / product).
3. Dense (when embeddings exist): cosine similarity with text-embedding-3-small.
4. Fusion: score = 0.5 * bm25_norm + 0.5 * cosine  (bm25-only when no vectors).
   Boosts: +0.08 if a product named in the query is tagged on the record,
   +0.05 if the record is an FAQ and the query is a question.
5. Grounding confidence (0..1) is *absolute*, not relative to the result list,
   so the voice agent can refuse to answer: it combines query-term coverage in
   the top record, raw BM25 strength and cosine. Below `GROUNDING_THRESHOLD`
   the agent says "I don't have that information" instead of guessing.
6. Citation = record_id + title + source file/locator + version, so every spoken
   answer can be traced to a line in a source document.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from shared.embeddings import cosine_sim_matrix, embed_texts

from .index import KBIndex, tokenize
from .ingest.normalizer import normalize_terminology
from .schema import KBRecord, RetrievalHit

# Three-tier grounding used by the voice agents:
#   confidence >= GROUNDING_THRESHOLD      -> answer from context, cite records
#   LOW_THRESHOLD <= confidence < GROUNDING -> LLM must verify the context really answers; else fallback
#   confidence < LOW_THRESHOLD              -> hard fallback ("I don't have that information"), no LLM call
GROUNDING_THRESHOLD = 0.55
LOW_THRESHOLD = 0.30

SYNONYMS: Dict[str, List[str]] = {
    "price": ["premium"], "cost": ["premium"], "costs": ["premium"], "cheap": ["premium", "discount"],
    "expensive": ["premium"], "kids": ["children"], "kid": ["children"], "child": ["children"],
    "parents": ["senior care"], "father": ["senior care"], "mother": ["senior care"], "elderly": ["senior care"],
    "old": ["age"], "hospital list": ["network hospitals"], "reject": ["rejected", "non-disclosure"],
    "sugar": ["diabetes"], "bp": ["hypertension"], "blood pressure": ["hypertension"], "smoke": ["tobacco"],
    "smoking": ["tobacco"], "cancel": ["free-look", "cancellation"], "refund": ["free-look"],
    "pregnancy": ["maternity"], "pregnant": ["maternity"], "baby": ["maternity", "newborn"],
    "dental": ["dental treatment"], "teeth": ["dental treatment"], "eye": ["cataract"], "cataract": ["specific illness"],
    "pay": ["payment"], "emi": ["monthly"], "installment": ["monthly"], "tax": ["section 80d"],
    "switch": ["portability"], "port": ["portability"], "transfer": ["portability"], "human": ["escalation"],
    "agent": ["advisor"], "manager": ["escalation"], "icu": ["room rent"], "room": ["room rent"],
    "bariatric": ["obesity", "weight-control"], "abroad": ["outside india"], "overseas": ["outside india"],
    "foreign": ["outside india"], "singapore": ["outside india"], "dubai": ["outside india"], "usa": ["outside india"],
    "ambulance": ["road ambulance"], "ayurveda": ["ayush"], "homeopathy": ["ayush"], "second opinion": ["escalation"],
    "after how long": ["waiting period", "maternity"],
    "difference between": ["family shield", "essential", "comparison"],
    "magkano": ["premium"], "aso": ["beneficiary"],
    "cicilan": ["angsuran", "installment"], "dp": ["down payment"], "denda": ["late fee"],
    "jatuh tempo": ["due date"], "tenor": ["term"],
}

_PRODUCT_Q = {
    "essential": re.compile(r"\bessential\b", re.I),
    "family_shield": re.compile(r"\bfamily (?:shield|floater|plan)\b", re.I),
    "senior_care": re.compile(r"\bsenior|parents?\b", re.I),
    "critical_illness_rider": re.compile(r"\bcritical illness\b", re.I),
}


def expand_query(q: str) -> str:
    q = normalize_terminology(q)
    low = q.lower()
    extra: List[str] = []
    for k, vs in SYNONYMS.items():
        if re.search(rf"\b{re.escape(k)}\b", low):
            extra.extend(vs)
    return q + (" " + " ".join(dict.fromkeys(extra)) if extra else "")


@dataclass
class SearchResponse:
    query: str
    expanded_query: str
    hits: List[RetrievalHit]
    confidence: float
    grounded: bool
    mode: str  # "hybrid" | "bm25"
    filters: Dict[str, Optional[str]] = field(default_factory=dict)

    def top(self) -> Optional[KBRecord]:
        return self.hits[0].record if self.hits else None

    @property
    def tier(self) -> str:
        if self.confidence >= GROUNDING_THRESHOLD:
            return "high"
        if self.confidence >= LOW_THRESHOLD:
            return "medium"
        return "low"

    def context_block(self, max_records: int = 4) -> str:
        """Formatted context for an LLM prompt, with citation tags."""
        parts = []
        for h in self.hits[:max_records]:
            parts.append(f"<<{h.record.record_id}>> ({h.record.title})\n{h.record.content}")
        return "\n\n".join(parts)

    def citations(self, max_records: int = 4) -> List[str]:
        return [h.record.citation() for h in self.hits[:max_records]]


class Retriever:
    def __init__(self, index: Optional[KBIndex] = None):
        self.index = index or KBIndex.load()

    def reload(self) -> None:
        self.index = KBIndex.load()

    def search(
        self,
        query: str,
        k: int = 5,
        *,
        market: Optional[str] = None,
        category: Optional[str] = None,
        intent: Optional[str] = None,
        product: Optional[str] = None,
        exclude_categories: Optional[List[str]] = None,
    ) -> SearchResponse:
        idx = self.index
        if not idx.records:
            return SearchResponse(query, query, [], 0.0, False, "bm25")
        expanded = expand_query(query)
        q_tokens = tokenize(expanded)

        # candidate mask
        mask = np.ones(len(idx.records), dtype=bool)
        for i, r in enumerate(idx.records):
            if market and r.market != market:
                mask[i] = False
            if category and r.category != category:
                mask[i] = False
            if intent and intent not in r.intent_types:
                mask[i] = False
            if product and product not in r.products:
                mask[i] = False
            if exclude_categories and r.category in exclude_categories:
                mask[i] = False
        if not mask.any():
            mask[:] = True

        bm25 = np.asarray(idx.bm25.get_scores(q_tokens), dtype=np.float32) if q_tokens else np.zeros(len(idx.records))
        bm25 = np.where(mask, bm25, 0.0)
        bm25_max = float(bm25.max()) if bm25.size else 0.0
        bm25_norm = bm25 / bm25_max if bm25_max > 0 else bm25

        mode = "bm25"
        cos = np.zeros(len(idx.records), dtype=np.float32)
        if idx.embeddings is not None:
            qv = embed_texts([expanded])
            if qv is not None:
                cos = cosine_sim_matrix(qv[0], idx.embeddings)
                cos = np.where(mask, cos, -1.0)
                mode = "hybrid"

        if mode == "hybrid":
            fused = 0.5 * bm25_norm + 0.5 * np.clip(cos, 0, 1)
        else:
            fused = bm25_norm.copy()

        q_products = [p for p, pat in _PRODUCT_Q.items() if pat.search(query)]
        is_question = query.strip().endswith("?") or bool(re.match(r"^(what|how|can|is|do|does|who|when|why|will|are)\b", query.strip(), re.I))
        for i, r in enumerate(idx.records):
            if not mask[i]:
                continue
            if q_products and any(p in r.products for p in q_products):
                fused[i] += 0.08
            if is_question and "faq" in r.tags:
                fused[i] += 0.05
        fused = np.where(mask, fused, -1.0)

        order = np.argsort(-fused)[: max(k, 1)]
        hits: List[RetrievalHit] = []
        for rank, i in enumerate(order, start=1):
            if fused[i] <= 0:
                continue
            r = idx.records[i]
            hits.append(RetrievalHit(record=r, score=float(fused[i]), bm25_score=float(bm25[i]),
                                     vector_score=float(cos[i]) if mode == "hybrid" else 0.0, rank=rank,
                                     explanation=self._explain(q_tokens, r, float(bm25[i]), float(cos[i]), mode)))

        confidence = self._confidence(q_tokens, hits, mode)
        # Hard out-of-scope cues: never let a weak lexical match look "grounded"
        if re.search(r"\b(stock price|share price|ceo|cfo|motor insurance|car insurance)\b", query, re.I):
            confidence = min(confidence, LOW_THRESHOLD - 0.01)
        return SearchResponse(query, expanded, hits, confidence, confidence >= GROUNDING_THRESHOLD, mode,
                              {"market": market, "category": category, "intent": intent, "product": product})

    # ---- helpers
    def _coverage(self, q_tokens: List[str], r: KBRecord) -> float:
        """IDF-weighted share of query terms present in the record.

        Unseen terms (e.g. 'ceo') get the corpus-max IDF, so a query whose
        distinctive word is missing from the KB scores low even if generic words match.
        """
        if not q_tokens:
            return 0.0
        idf = self.index.bm25.idf if self.index.bm25 is not None else {}
        max_idf = max(idf.values()) if idf else 1.0
        rt = set(tokenize(f"{r.title} {r.content}"))
        weights = {t: max(idf.get(t, max_idf), 0.1) for t in set(q_tokens)}
        total = sum(weights.values())
        return sum(w for t, w in weights.items() if t in rt) / total if total else 0.0

    def _confidence(self, q_tokens: List[str], hits: List[RetrievalHit], mode: str) -> float:
        if not hits:
            return 0.0
        top = hits[0]
        cov = self._coverage(q_tokens, top.record)
        bm_strength = min(1.0, top.bm25_score / 12.0)  # ~12+ is a strong BM25 match on this corpus
        if mode == "hybrid":
            return round(0.4 * cov + 0.2 * bm_strength + 0.4 * max(0.0, top.vector_score), 3)
        return round(0.65 * cov + 0.35 * bm_strength, 3)

    def _explain(self, q_tokens: List[str], r: KBRecord, bm: float, cos: float, mode: str) -> str:
        rt = set(tokenize(f"{r.title} {r.content}"))
        matched = [t for t in dict.fromkeys(q_tokens) if t in rt]
        s = f"matched terms: {', '.join(matched) or 'none'}; bm25={bm:.2f}"
        if mode == "hybrid":
            s += f"; cosine={cos:.2f}"
        return s


_retriever: Optional[Retriever] = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever
