"""Embedding client with a persistent on-disk cache (keyed by model + text hash).

If no OpenAI key is configured `embed_texts` returns None and the KB falls back
to BM25-only retrieval. This keeps the whole repo runnable offline.
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import List, Optional

import numpy as np

from .config import CACHE_DIR, settings
from .llm import get_client

log = logging.getLogger(__name__)
_CACHE_FILE = CACHE_DIR / "embeddings_cache.jsonl"
_cache: dict[str, List[float]] = {}
_loaded = False


def _key(text: str, model: str) -> str:
    return hashlib.sha1(f"{model}::{text}".encode("utf-8")).hexdigest()


def _load_cache() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    if _CACHE_FILE.exists():
        with _CACHE_FILE.open("r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                    _cache[rec["k"]] = rec["v"]
                except Exception:  # noqa: BLE001 - corrupted cache line, skip
                    continue


def _append_cache(key: str, vec: List[float]) -> None:
    _cache[key] = vec
    with _CACHE_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"k": key, "v": vec}) + "\n")


def embeddings_available() -> bool:
    return get_client() is not None


def embed_texts(texts: List[str], batch_size: int = 64) -> Optional[np.ndarray]:
    """Return an (n, d) float32 array or None if embeddings are unavailable."""
    client = get_client()
    if client is None:
        return None
    _load_cache()
    model = settings.active_embedding_model
    out: List[Optional[List[float]]] = [None] * len(texts)
    todo_idx: List[int] = []
    for i, t in enumerate(texts):
        k = _key(t, model)
        if k in _cache:
            out[i] = _cache[k]
        else:
            todo_idx.append(i)

    for start in range(0, len(todo_idx), batch_size):
        batch_ids = todo_idx[start : start + batch_size]
        batch = [texts[i].replace("\n", " ") for i in batch_ids]
        try:
            resp = client.embeddings.create(model=model, input=batch)
            for j, item in enumerate(resp.data):
                idx = batch_ids[j]
                out[idx] = item.embedding
                _append_cache(_key(texts[idx], model), item.embedding)
        except Exception as exc:
            log.warning("Embedding call failed (%s); falling back to BM25: %s", model, exc)
            return None

    return np.asarray(out, dtype=np.float32)


def cosine_sim_matrix(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    q = query / (np.linalg.norm(query) + 1e-9)
    m = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9)
    return m @ q
