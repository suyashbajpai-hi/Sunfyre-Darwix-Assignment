"""FastAPI router for the knowledge base: search, record lookup, stats, UI."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from shared.config import KB_DIR

from .retriever import get_retriever

router = APIRouter(prefix="/kb", tags=["Q2 Knowledge Base"])
_UI = Path(__file__).parent / "static" / "kb.html"


@router.get("/search")
def search(q: str = Query(..., min_length=2), k: int = 5, market: Optional[str] = None,
           category: Optional[str] = None, intent: Optional[str] = None, product: Optional[str] = None):
    res = get_retriever().search(q, k=k, market=market, category=category, intent=intent, product=product)
    return {
        "query": res.query, "expanded_query": res.expanded_query, "mode": res.mode,
        "confidence": res.confidence, "tier": res.tier, "grounded": res.grounded,
        "hits": [
            {
                "rank": h.rank, "score": round(h.score, 3), "bm25": round(h.bm25_score, 2),
                "cosine": round(h.vector_score, 3), "record_id": h.record.record_id, "title": h.record.title,
                "content": h.record.content, "category": h.record.category, "products": h.record.products,
                "source": h.record.source.model_dump(), "version": h.record.version, "pii": h.record.pii,
                "citation": h.record.citation(), "explanation": h.explanation, "market": h.record.market,
            }
            for h in res.hits
        ],
    }


@router.get("/records/{record_id}")
def get_record(record_id: str):
    rec = get_retriever().index.by_id.get(record_id)
    if not rec:
        raise HTTPException(404, "record not found")
    return rec.model_dump()


@router.get("/stats")
def stats():
    manifest = KB_DIR / "manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {}
    idx = get_retriever().index
    data["active_records"] = len(idx.records)
    data["superseded_records"] = len(idx.all_records) - len(idx.records)
    data["dense_index"] = idx.embeddings is not None
    return data


@router.post("/reload")
def reload():
    get_retriever().reload()
    return {"ok": True}


@router.get("", response_class=HTMLResponse, include_in_schema=False)
def ui():
    return HTMLResponse(_UI.read_text(encoding="utf-8"),
                        headers={"Cache-Control": "no-store, no-cache, must-revalidate"})
