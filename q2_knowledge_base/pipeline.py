"""End-to-end KB build: sources -> cleaned docs -> records -> index -> reports.

    python -m q2_knowledge_base.pipeline            # build IN (Q1) + PH/ID (Q3) markets
    python -m q2_knowledge_base.pipeline --no-embed # BM25 only (no API calls)

Versioning
----------
* `kb_version` = YYYY.MM.DD-N where N increments when the record content hash
  set differs from the previous manifest built the same day.
* Each record carries its own `version`; if a record_id existed before with a
  different content_hash its minor version is bumped (1.0 -> 1.1).
* Source files are hashed into the manifest so a rebuild can prove which inputs
  produced which KB.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Tuple

from shared.config import KB_DIR, ROOT_DIR, settings
from shared.pii import mask_text

from .index import MANIFEST_FILE, KBIndex
from .ingest.chunker import chunk_document
from .ingest.cleaner import clean_documents
from .ingest.dedup import dedup_records
from .ingest.loaders import load_source
from .ingest.normalizer import normalize_text
from .ingest.quality import flag_documents, flag_records
from .ingest.taxonomy import classify
from .schema import KBRecord, Manifest, SourceDocument

log = logging.getLogger("kb.pipeline")

# (root, market, language) - Q3 locale packs plug into the same pipeline
SOURCE_ROOTS: List[Tuple[Path, str, str]] = [
    (ROOT_DIR / "q2_knowledge_base" / "sources", "IN", "en"),
    (ROOT_DIR / "q3_native_bots" / "philippines" / "kb_sources", "PH", "fil"),
    (ROOT_DIR / "q3_native_bots" / "indonesia" / "kb_sources", "ID", "id"),
]
SKIP_FILES = {"build_pdf_sources.py", "__init__.py"}


def discover_sources() -> List[Tuple[Path, Path, str, str]]:
    out = []
    for root, market, lang in SOURCE_ROOTS:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*")):
            rel_parts = p.relative_to(root).parts
            if any(part.startswith((".", "_")) for part in rel_parts):
                continue  # hidden dirs, __pycache__ ...
            if p.is_file() and p.name not in SKIP_FILES:
                out.append((p, root, market, lang))
    return out


def _assign_ids(records: List[KBRecord], previous: Dict[str, str]) -> None:
    counters: Counter = Counter()
    for r in records:
        key = f"{r.market.lower()}_{r.category}"
        counters[key] += 1
        r.record_id = f"kb_{key}_{counters[key]:03d}"
        r.compute_hash()
        prev_hash = previous.get(r.record_id)
        if prev_hash and prev_hash != r.content_hash:
            major, minor = r.version.split(".")
            r.version = f"{major}.{int(minor) + 1}"


def _kb_version(record_hashes: List[str]) -> str:
    today = date.today().strftime("%Y.%m.%d")
    digest = hashlib.sha1("".join(sorted(record_hashes)).encode()).hexdigest()[:8]
    n = 1
    if MANIFEST_FILE.exists():
        try:
            prev = json.loads(MANIFEST_FILE.read_text())
            pv = prev.get("kb_version", "")
            if pv.startswith(today):
                n = int(pv.split("-")[1]) + (0 if prev.get("content_digest") == digest else 1)
        except Exception:  # noqa: BLE001
            pass
    return f"{today}-{n}", digest


def build(embed: bool = True) -> Manifest:
    logging.basicConfig(level=settings.log_level, format="%(levelname)s %(name)s: %(message)s")
    previous: Dict[str, str] = {}
    if (KB_DIR / "records.jsonl").exists():
        for line in (KB_DIR / "records.jsonl").read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(line)
                previous[d["record_id"]] = d["content_hash"]
            except Exception:  # noqa: BLE001
                continue

    # 1. load
    docs: List[SourceDocument] = []
    source_hashes: Dict[str, str] = {}
    for path, root, market, lang in discover_sources():
        doc = load_source(path, root, market, lang)
        source_hashes[f"{market}/{doc.file}"] = hashlib.sha1(path.read_bytes()).hexdigest()[:12]
        docs.append(doc)
        log.info("loaded %-55s status=%-6s sections=%d", f"{market}/{doc.file}", doc.status, len(doc.sections))

    # 2. clean + normalise
    clean_stats = clean_documents(docs, repeat_threshold=2)
    for d in docs:
        for s in d.sections:
            s.text = normalize_text(s.text)
        d.title = normalize_text(d.title)
    flag_documents(docs)

    # 3. chunk + PII + classify
    records: List[KBRecord] = []
    pii_stats = Counter()
    for d in docs:
        if d.status != "ok":
            continue
        for rec in chunk_document(d):
            masked, kinds = mask_text(rec.content)
            if kinds:
                rec.content, rec.pii, rec.pii_types = masked, True, kinds
                pii_stats.update(kinds)
            classify(rec)
            records.append(rec)

    # 4. dedup (needs ids for traceability -> assign provisional ids first)
    _assign_ids(records, previous)
    dedup_stats = dedup_records(records)
    quality_report = flag_records(records)

    # 5. index
    index = KBIndex(records)
    embedded = index.build_embeddings() if embed else False

    kb_version, digest = _kb_version([r.content_hash for r in records])
    for r in records:
        r.kb_version = kb_version
    manifest = Manifest(
        kb_version=kb_version,
        built_at=datetime.now().isoformat(timespec="seconds"),
        record_count=len(index.records),
        document_count=sum(1 for d in docs if d.status == "ok"),
        failed_documents=[f"{d.file}: {d.error}" for d in docs if d.status != "ok"],
        superseded_documents=[d.file for d in docs if d.superseded],
        categories=dict(Counter(r.category for r in index.records)),
        markets=dict(Counter(r.market for r in index.records)),
        embedding_model=settings.embedding_model if embedded else None,
        source_hashes=source_hashes,
    )
    manifest_dict = manifest.model_dump()
    manifest_dict["content_digest"] = digest
    index.save(manifest)
    MANIFEST_FILE.write_text(json.dumps(manifest_dict, indent=2), encoding="utf-8")

    _write_quality_report(docs, records, clean_stats, dedup_stats, pii_stats, quality_report, manifest)
    _write_sample_records(index.records)
    log.info("KB built: version=%s records=%d (superseded %d) embedded=%s", kb_version, len(index.records),
             len(records) - len(index.records), embedded)
    return manifest


def _write_quality_report(docs, records, clean_stats, dedup_stats, pii_stats, quality_report, manifest) -> None:
    lines = [f"# Knowledge Base Build Report - {manifest.kb_version}", "", f"Built at {manifest.built_at}", "",
             "## Documents", "", "| Source | Type | Market | Status | Sections | Raw chars | Clean chars | Version | Date | Flags |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for d in docs:
        lines.append(f"| {d.file} | {d.source_type} | {d.market} | {d.status}{' - ' + d.error if d.error else ''} | "
                     f"{len(d.sections)} | {d.raw_chars} | {d.clean_chars} | {d.doc_version} | {d.doc_date or ''} | "
                     f"{', '.join(d.flags) or ''} |")
    lines += ["", "## Cleaning", ""] + [f"- {k}: {v}" for k, v in clean_stats.items()]
    lines += ["", "## De-duplication", ""] + [f"- {k}: {v}" for k, v in dedup_stats.items()]
    sup = [r for r in records if r.superseded]
    if sup:
        lines += ["", "Superseded chunks (kept for traceability, excluded from retrieval):", ""]
        for r in sup[:40]:
            lines.append(f"- `{r.record_id}` ({r.source.file}) - {'; '.join(f for f in r.quality_flags if 'duplicate' in f) or 'older edition'}")
    lines += ["", "## PII protection", "", f"Records with PII masked: {sum(1 for r in records if r.pii)}", ""]
    lines += [f"- {k}: {v} occurrences" for k, v in pii_stats.items()]
    lines += ["", "## Source errors / conflicts flagged", ""]
    if not quality_report:
        lines.append("None detected.")
    for flag, items in quality_report.items():
        lines.append(f"- **{flag}**: " + "; ".join(items))
    lines += ["", "## Records by category", ""] + [f"- {k}: {v}" for k, v in sorted(manifest.categories.items())]
    lines += ["", "## Records by market", ""] + [f"- {k}: {v}" for k, v in manifest.markets.items()]
    lines += ["", f"Embedding model: {manifest.embedding_model or 'none (BM25 only)'}", ""]
    (KB_DIR / "build_report.md").write_text("\n".join(lines), encoding="utf-8")


def _write_sample_records(records: List[KBRecord]) -> None:
    seen = set()
    samples = []
    for r in records:
        if r.category not in seen:
            seen.add(r.category)
            samples.append(r.model_dump())
    (KB_DIR / "sample_records.json").write_text(json.dumps(samples, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-embed", action="store_true", help="skip dense embeddings (BM25 only)")
    args = ap.parse_args()
    m = build(embed=not args.no_embed)
    print(json.dumps({"kb_version": m.kb_version, "records": m.record_count, "documents": m.document_count,
                      "failed": m.failed_documents, "categories": m.categories}, indent=2))
