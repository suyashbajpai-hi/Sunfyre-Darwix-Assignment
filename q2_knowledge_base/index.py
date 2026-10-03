"""Index persistence: records.jsonl + embeddings.npy + manifest.json.

Embedding/indexing approach
---------------------------
* Sparse: BM25Okapi over lowercased alphanumeric tokens of `title + content`
  (title tokens repeated once to up-weight them). Rebuilt at load time - it is
  a few hundred documents and takes milliseconds.
* Dense: OpenAI `text-embedding-3-small` (1536-d) over `title + "\n" + content`,
  cached on disk by content hash so re-indexing only embeds changed chunks.
  Stored as float32 .npy aligned with the active (non-superseded) record order.
* At scale, the dense side would move to a vector DB (pgvector / Qdrant) with the
  same record_id as the key, and BM25 to OpenSearch - the retrieval API does not
  change.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Optional

import numpy as np
from rank_bm25 import BM25Okapi

from shared.config import KB_DIR
from shared.embeddings import embed_texts, embeddings_available

from .schema import KBRecord, Manifest

RECORDS_FILE = KB_DIR / "records.jsonl"
EMB_FILE = KB_DIR / "index" / "embeddings.npy"
EMB_IDS_FILE = KB_DIR / "index" / "embedding_ids.json"
MANIFEST_FILE = KB_DIR / "manifest.json"

_TOKEN = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)?")
_STOP = {"the", "a", "an", "of", "to", "and", "or", "is", "are", "in", "on", "for", "with", "at", "by", "be", "it",
         "this", "that", "as", "from", "we", "you", "your", "our", "i", "my", "do", "does", "can", "what", "how", "any",
         "who", "whose", "whom", "which", "where", "when", "why", "would", "could", "should", "will", "want", "need",
         "get", "much", "many", "there", "about", "me", "us", "they", "their", "them", "if", "not", "no", "yes", "ok",
         "please", "tell", "know", "like", "just", "also", "than", "then", "so", "but", "am", "was", "were", "been",
         "has", "have", "had", "into", "out", "up", "down", "over", "its", "he", "she", "his", "her", "say", "said",
         # Filipino / Tagalog function words
         "ang", "ng", "sa", "na", "ay", "mga", "po", "opo", "yung", "lang", "naman", "kung", "para", "ako", "ko",
         "mo", "ka", "ba", "ho", "siya", "namin", "natin", "kayo", "sila",
         # Bahasa Indonesia function words
         "yang", "dan", "di", "ke", "ini", "itu", "pak", "bu", "ya", "dong", "sih", "nya", "ada", "tidak", "bisa",
         "untuk", "dengan", "dari", "pada", "atau", "juga", "saya", "anda", "kami", "kita", "tidak", "sudah"}


def tokenize(text: str) -> List[str]:
    toks = []
    for t in _TOKEN.findall(text.lower()):
        if t in _STOP or len(t) < 2:
            continue
        # light stemming: plural / -ing / -ed
        if len(t) > 4 and t.endswith("ies"):
            t = t[:-3] + "y"
        elif len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]
        toks.append(t)
    return toks


def record_text(r: KBRecord) -> str:
    return f"{r.title}\n{r.title}\n{r.content}"


class KBIndex:
    def __init__(self, records: List[KBRecord], embeddings: Optional[np.ndarray] = None):
        self.all_records = records
        self.records = [r for r in records if not r.superseded]
        self.by_id = {r.record_id: r for r in records}
        self.bm25 = BM25Okapi([tokenize(record_text(r)) for r in self.records]) if self.records else None
        self.embeddings = embeddings  # aligned with self.records

    # ---- persistence
    @classmethod
    def load(cls) -> "KBIndex":
        if not RECORDS_FILE.exists():
            raise FileNotFoundError("KB not built. Run: python -m q2_knowledge_base.pipeline")
        records = [KBRecord.model_validate_json(line) for line in RECORDS_FILE.read_text(encoding="utf-8").splitlines()
                   if line.strip()]
        emb = None
        if EMB_FILE.exists() and EMB_IDS_FILE.exists():
            ids = json.loads(EMB_IDS_FILE.read_text())
            active_ids = [r.record_id for r in records if not r.superseded]
            if ids == active_ids:
                emb = np.load(EMB_FILE)
        return cls(records, emb)

    def save(self, manifest: Manifest) -> None:
        KB_DIR.mkdir(parents=True, exist_ok=True)
        (KB_DIR / "index").mkdir(exist_ok=True)
        with RECORDS_FILE.open("w", encoding="utf-8") as fh:
            for r in self.all_records:
                fh.write(r.model_dump_json() + "\n")
        if self.embeddings is not None:
            np.save(EMB_FILE, self.embeddings)
            EMB_IDS_FILE.write_text(json.dumps([r.record_id for r in self.records]))
        MANIFEST_FILE.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    def build_embeddings(self) -> bool:
        if not embeddings_available() or not self.records:
            return False
        self.embeddings = embed_texts([f"{r.title}\n{r.content}" for r in self.records])
        return self.embeddings is not None
