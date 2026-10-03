"""Knowledge-base document schema.

A *SourceDocument* is the parsed, cleaned representation of one input file.
A *KBRecord* is one retrievable chunk with full provenance.

Record example (also in docs/q2_knowledge_base.md):

    record_id      kb_eligibility_underwriting_003
    title          Underwriting & Qualification Rules > Entry Age
    content        Essential and Family Shield: adults aged 18 to 65 years at policy start ...
    category       eligibility_underwriting
    products       ["essential", "family_shield", "senior_care"]
    source         {"file": "docs/underwriting_rules.md", "type": "markdown", "locator": "## 1. Entry age", "doc_version": "3.2"}
    version        1.0            (record version; bumps when content hash changes)
    kb_version     2024.10.01-1   (whole-KB build version)
    pii            false
    market/lang    IN / en
"""
from __future__ import annotations

import hashlib
from datetime import date
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

SourceType = Literal["html", "pdf", "markdown", "text", "csv", "json_form"]
Status = Literal["ok", "failed", "empty"]


class Section(BaseModel):
    heading_path: List[str] = Field(default_factory=list)  # e.g. ["Plans", "Sentinel Essential"]
    text: str
    locator: str = ""  # page number, heading anchor, row range...
    kind: Literal["prose", "table", "list", "form", "faq"] = "prose"


class SourceDocument(BaseModel):
    doc_id: str
    file: str  # path relative to the sources root
    source_type: SourceType
    title: str = ""
    market: str = "IN"
    language: str = "en"
    doc_version: str = "1.0"
    doc_date: Optional[str] = None  # ISO date if found
    status: Status = "ok"
    error: Optional[str] = None
    sections: List[Section] = Field(default_factory=list)
    raw_chars: int = 0
    clean_chars: int = 0
    flags: List[str] = Field(default_factory=list)  # quality flags: outdated, zero_premium, conflict ...
    superseded: bool = False


class SourceRef(BaseModel):
    file: str
    type: SourceType
    locator: str = ""
    doc_version: str = "1.0"
    doc_date: Optional[str] = None
    url: Optional[str] = None


class KBRecord(BaseModel):
    record_id: str
    title: str
    content: str
    category: str
    subcategory: Optional[str] = None
    products: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    intent_types: List[str] = Field(default_factory=list)  # product, policy, qualification, faq, objection, compliance
    source: SourceRef
    market: str = "IN"
    language: str = "en"
    version: str = "1.0"
    kb_version: str = ""
    content_hash: str = ""
    pii: bool = False
    pii_types: List[str] = Field(default_factory=list)
    chunk_index: int = 0
    parent_doc_id: str = ""
    superseded: bool = False
    quality_flags: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: date.today().isoformat())
    token_estimate: int = 0

    def compute_hash(self) -> str:
        self.content_hash = hashlib.sha1(f"{self.title}\n{self.content}".encode("utf-8")).hexdigest()[:16]
        return self.content_hash

    def citation(self) -> str:
        loc = f" § {self.source.locator}" if self.source.locator else ""
        return f"[{self.record_id} | {self.title} | {self.source.file}{loc} | v{self.version}]"


class RetrievalHit(BaseModel):
    record: KBRecord
    score: float
    bm25_score: float = 0.0
    vector_score: float = 0.0
    rank: int = 0
    explanation: str = ""


class Manifest(BaseModel):
    kb_version: str
    built_at: str
    record_count: int
    document_count: int
    failed_documents: List[str] = Field(default_factory=list)
    superseded_documents: List[str] = Field(default_factory=list)
    categories: Dict[str, int] = Field(default_factory=dict)
    markets: Dict[str, int] = Field(default_factory=dict)
    embedding_model: Optional[str] = None
    source_hashes: Dict[str, str] = Field(default_factory=dict)
