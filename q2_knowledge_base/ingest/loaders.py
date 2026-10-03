"""Source loaders: turn a file into a SourceDocument with heading-aware sections.

Website extraction
------------------
In production the HTML would come from a crawler (requests + sitemap, or a
headless browser for JS-heavy pages). Here the pages are stored on disk. The
extraction logic is identical: parse with BeautifulSoup, drop `<nav>`, `<header>`,
`<footer>`, `<script>`, `<style>`, cookie banners and promo asides, keep `<main>`
(or `<body>` when no main), and walk headings to build a heading path for each
paragraph / list / table.

Document parsing
----------------
* PDF  -> pypdf text extraction, page by page (locator = page number). Lines that
          look like headings ("SECTION A - ...", "A.1 ...") open new sections.
* MD   -> headings via `#` levels, tables kept as table sections.
* TXT  -> blank-line paragraphs; ALL-CAPS lines are treated as headings.
* CSV  -> each row becomes a sentence using the header names (table-to-text).
* JSON form -> each section's fields become a "form" section with standardised
          field names.

Extraction failures are caught and returned as `status="failed"` documents so the
pipeline can report them instead of crashing.
"""
from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup, Tag

from ..schema import Section, SourceDocument
from .normalizer import standardize_field_name, standardize_heading

BOILERPLATE_SELECTORS = [
    "nav", "header", "footer", "script", "style", "noscript", ".cookie-banner", ".promo", ".site-header",
    ".site-footer", "aside", "[role=navigation]", ".breadcrumbs", ".share", ".social",
]

_VERSION_RE = re.compile(r"\b(?:Version|v)\s*([0-9]+(?:\.[0-9]+)+|[0-9]{4}\.[0-9]+)\b", re.I)
_MONTHS = {m.lower()[:3]: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
     "December"], start=1)}


def _mon(s: str) -> Optional[int]:
    return _MONTHS.get(s[:3].lower())


# (pattern, converter(groups) -> ISO or None)
_DATE_PATTERNS = [
    (re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"), lambda g: f"{g[0]}-{g[1]}-{g[2]}"),
    (re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b"), lambda g: f"{g[2]}-{int(g[1]):02d}-{int(g[0]):02d}"),
    (re.compile(r"\b(\d{1,2})-([A-Za-z]{3})-(\d{4})\b"),
     lambda g: f"{g[2]}-{_mon(g[1]):02d}-{int(g[0]):02d}" if _mon(g[1]) else None),
    (re.compile(r"\b([A-Z][a-z]{2,8})\s+(\d{1,2}),\s+(\d{4})\b"),
     lambda g: f"{g[2]}-{_mon(g[0]):02d}-{int(g[1]):02d}" if _mon(g[0]) else None),
    (re.compile(r"\b(\d{1,2})\s+([A-Z][a-z]{2,8})\s+(\d{4})\b"),
     lambda g: f"{g[2]}-{_mon(g[1]):02d}-{int(g[0]):02d}" if _mon(g[1]) else None),
    (re.compile(r"\b([A-Z][a-z]{2,8})[\s-](\d{4})\b"),  # "October 2023" / "Oct-2023" -> first of month
     lambda g: f"{g[1]}-{_mon(g[0]):02d}-01" if _mon(g[0]) else None),
]


def _first_date(text: str) -> Optional[str]:
    """Earliest-positioned date in the document head (dates near the title are the document date)."""
    head = text[:600]
    best: Optional[tuple[int, str]] = None
    for pat, conv in _DATE_PATTERNS:
        for m in pat.finditer(head):
            try:
                iso = conv(m.groups())
            except (ValueError, TypeError):
                iso = None
            if iso and (best is None or m.start() < best[0]):
                best = (m.start(), iso)
    return best[1] if best else None


def _doc_meta(text: str) -> tuple[str, Optional[str]]:
    m = _VERSION_RE.search(text[:800])
    return (m.group(1) if m else "1.0"), _first_date(text)


# --------------------------------------------------------------------------- HTML

def _table_to_sections(table: Tag, heading_path: List[str]) -> List[Section]:
    rows = table.find_all("tr")
    if not rows:
        return []
    header = [c.get_text(" ", strip=True) for c in rows[0].find_all(["th", "td"])]
    lines = []
    for tr in rows[1:]:
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        if not cells:
            continue
        if header and len(cells) == len(header) and len(header) > 1:
            feature = cells[0]
            parts = [f"{header[i]}: {cells[i]}" for i in range(1, len(cells))]
            lines.append(f"{feature} - " + "; ".join(parts) + ".")
        else:
            lines.append(" | ".join(cells))
    text = "\n".join(lines)
    return [Section(heading_path=heading_path, text=text, kind="table", locator="table")] if text else []


def load_html(path: Path, rel: str) -> SourceDocument:
    html = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True).split("|")[0].strip() if soup.title else path.stem
    for sel in BOILERPLATE_SELECTORS:
        for el in soup.select(sel):
            el.decompose()
    root = soup.find("main") or soup.body or soup

    sections: List[Section] = []
    path_stack: List[str] = []
    buf: List[str] = []
    kind = "prose"
    locator = ""

    def flush():
        nonlocal buf, kind
        if buf:
            sections.append(Section(heading_path=list(path_stack), text="\n".join(buf).strip(), kind=kind,
                                    locator=locator or " > ".join(path_stack)))
        buf = []
        kind = "prose"

    for el in root.descendants:
        if not isinstance(el, Tag):
            continue
        name = el.name
        if name in {"h1", "h2", "h3", "h4"}:
            flush()
            level = int(name[1])
            text = standardize_heading(el.get_text(" ", strip=True))
            del path_stack[level - 1:]
            while len(path_stack) < level - 1:
                path_stack.append("")
            path_stack.append(text)
            path_stack[:] = [p for p in path_stack if p]
            locator = el.get("id") or text
            if name == "h3" and path_stack and "faq" in rel.lower():
                kind = "faq"
        elif name == "p" and not el.find_parent("li"):
            t = el.get_text(" ", strip=True)
            if t:
                buf.append(t)
        elif name in {"ul", "ol"} and not el.find_parent(["ul", "ol"]):
            items = [li.get_text(" ", strip=True) for li in el.find_all("li", recursive=False)]
            if items:
                buf.extend(f"- {it}" for it in items)
                if kind == "prose":
                    kind = "list"
        elif name == "table":
            flush()
            sections.extend(_table_to_sections(el, list(path_stack)))
    flush()
    doc = SourceDocument(doc_id=_doc_id(rel), file=rel, source_type="html", title=title, sections=sections,
                         raw_chars=len(html))
    all_text = "\n".join(s.text for s in sections)
    doc.doc_version, doc.doc_date = _doc_meta(all_text + " " + html[-1500:])
    # "last updated" dates on web pages are usually near the bottom
    m = re.search(r"last updated on (\d{2})/(\d{2})/(\d{4})", html)
    if m:
        doc.doc_date = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return doc


# --------------------------------------------------------------------------- PDF

_PDF_HEADING = re.compile(r"^(SECTION [A-Z]\b.*|[A-Z]\.\d+\s.*|[A-Z][A-Z &-]{6,}$)")


def load_pdf(path: Path, rel: str) -> SourceDocument:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    sections: List[Section] = []
    heading_path: List[str] = []
    title = path.stem.replace("_", " ").title()
    full = []
    for pno, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        full.append(text)
        buf: List[str] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if _PDF_HEADING.match(line) and len(line) < 90:
                if buf:
                    sections.append(Section(heading_path=list(heading_path), text=" ".join(buf), locator=f"page {pno}"))
                    buf = []
                if line.startswith("SECTION"):
                    heading_path = [standardize_heading(line)]
                else:
                    heading_path = heading_path[:1] + [standardize_heading(line.split(" ", 1)[1] if " " in line else line)]
                    buf.append(line)
            else:
                buf.append(line)
        if buf:
            sections.append(Section(heading_path=list(heading_path), text=" ".join(buf), locator=f"page {pno}"))
    if not sections:
        raise ValueError("no extractable text (scanned image or empty PDF)")
    joined = "\n".join(full)
    first_line = joined.strip().splitlines()[0] if joined.strip() else title
    doc = SourceDocument(doc_id=_doc_id(rel), file=rel, source_type="pdf", title=first_line.title()[:80],
                         sections=sections, raw_chars=len(joined))
    doc.doc_version, doc.doc_date = _doc_meta(joined)
    return doc


# --------------------------------------------------------------------------- Markdown / Text

def load_markdown(path: Path, rel: str) -> SourceDocument:
    text = path.read_text(encoding="utf-8", errors="replace")
    sections: List[Section] = []
    heading_path: List[str] = []
    buf: List[str] = []
    table_buf: List[str] = []
    title = path.stem.replace("_", " ").title()

    def flush():
        nonlocal buf, table_buf
        if table_buf:
            sections.append(Section(heading_path=list(heading_path), text=_md_table_to_text(table_buf), kind="table",
                                    locator=" > ".join(heading_path)))
            table_buf = []
        if buf:
            sections.append(Section(heading_path=list(heading_path), text="\n".join(buf).strip(),
                                    locator=" > ".join(heading_path)))
            buf = []

    for line in text.splitlines():
        if line.startswith("#"):
            flush()
            level = len(line) - len(line.lstrip("#"))
            heading = standardize_heading(line.lstrip("#").strip())
            if level == 1:
                title = heading
                heading_path = []
                continue
            heading_path = heading_path[: level - 2] + [heading]
        elif line.strip().startswith("|"):
            table_buf.append(line.strip())
        elif not line.strip():
            if table_buf:
                flush()
            elif buf:
                buf.append("")
        else:
            buf.append(line.rstrip())
    flush()
    for s in sections:
        s.text = re.sub(r"\n{2,}", "\n", s.text).strip()
    doc = SourceDocument(doc_id=_doc_id(rel), file=rel, source_type="markdown", title=title, sections=sections,
                         raw_chars=len(text))
    doc.doc_version, doc.doc_date = _doc_meta(text)
    return doc


def _md_table_to_text(lines: List[str]) -> str:
    rows = [[c.strip() for c in ln.strip("|").split("|")] for ln in lines if not re.match(r"^\|?\s*-+", ln)]
    if not rows:
        return ""
    header, body = rows[0], rows[1:]
    out = []
    for r in body:
        if len(r) != len(header):
            out.append(" | ".join(r))
            continue
        out.append(f"{r[0]} - " + "; ".join(f"{header[i]}: {r[i]}" for i in range(1, len(r))) + ".")
    return "\n".join(out)


def load_text(path: Path, rel: str) -> SourceDocument:
    text = path.read_text(encoding="utf-8", errors="replace")
    paras = [p.strip() for p in re.split(r"\n\s*\n|\n-----\n", text) if p.strip()]
    sections: List[Section] = []
    heading_path: List[str] = []
    title = paras[0].splitlines()[0].title() if paras else path.stem
    for p in paras:
        lines = p.splitlines()
        if len(lines) == 1 and lines[0].isupper() and len(lines[0]) < 80:
            heading_path = [standardize_heading(lines[0])]
            continue
        if lines[0].isupper() and len(lines[0]) < 80:
            heading_path = [standardize_heading(lines[0])]
            p = "\n".join(lines[1:])
        sections.append(Section(heading_path=list(heading_path), text=p.strip(), locator=" > ".join(heading_path)))
    doc = SourceDocument(doc_id=_doc_id(rel), file=rel, source_type="text", title=title, sections=sections,
                         raw_chars=len(text))
    doc.doc_version, doc.doc_date = _doc_meta(text)
    return doc


# --------------------------------------------------------------------------- CSV / JSON

def load_csv(path: Path, rel: str) -> SourceDocument:
    text = path.read_text(encoding="utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise ValueError("CSV has no data rows")
    sections: List[Section] = []
    # group rows by first column (plan) so a chunk = one plan's rate table
    groups: dict[str, List[str]] = {}
    first_col = reader.fieldnames[0]
    for i, row in enumerate(rows, start=2):
        parts = []
        for k, v in row.items():
            if v is None or v == "":
                continue
            parts.append(f"{standardize_field_name(k).replace('_', ' ')}: {v}")
        groups.setdefault(row[first_col], []).append(f"(row {i}) " + "; ".join(parts) + ".")
    for key, lines in groups.items():
        sections.append(Section(heading_path=[key], text="\n".join(lines), kind="table", locator=f"rows for {key}"))
    doc = SourceDocument(doc_id=_doc_id(rel), file=rel, source_type="csv", title=path.stem.replace("_", " ").title(),
                         sections=sections, raw_chars=len(text))
    return doc


def load_json_form(path: Path, rel: str) -> SourceDocument:
    data = json.loads(path.read_text(encoding="utf-8"))
    sections: List[Section] = []
    for sec in data.get("sections", []):
        lines = []
        for f in sec.get("fields", []):
            name = standardize_field_name(f.get("name", ""))
            req = "required" if f.get("required") else "optional"
            opts = f" Options: {', '.join(map(str, f['options']))}." if f.get("options") else ""
            help_ = f" {f['help']}." if f.get("help") else ""
            lines.append(f"Field {name} ({f.get('type', 'text')}, {req}): {f.get('label', '')}.{opts}{help_}")
        sections.append(Section(heading_path=[sec.get("title", "")], text="\n".join(lines), kind="form",
                                locator=sec.get("title", "")))
    doc = SourceDocument(doc_id=_doc_id(rel), file=rel, source_type="json_form", title=data.get("form_name", path.stem),
                         sections=sections, raw_chars=path.stat().st_size, doc_version=str(data.get("version", "1.0")))
    return doc


# --------------------------------------------------------------------------- dispatcher

def _doc_id(rel: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", rel.lower()).strip("_")


LOADERS = {
    ".html": load_html, ".htm": load_html, ".pdf": load_pdf, ".md": load_markdown, ".txt": load_text,
    ".csv": load_csv, ".json": load_json_form,
}


def load_source(path: Path, root: Path, market: str = "IN", language: str = "en") -> SourceDocument:
    rel = path.relative_to(root).as_posix()
    loader = LOADERS.get(path.suffix.lower())
    if loader is None:
        return SourceDocument(doc_id=_doc_id(rel), file=rel, source_type="text", status="failed",
                              error=f"unsupported file type {path.suffix}", market=market, language=language)
    try:
        doc = loader(path, rel)
        doc.market, doc.language = market, language
        if not any(s.text.strip() for s in doc.sections):
            doc.status, doc.error = "empty", "no content after extraction"
        return doc
    except Exception as exc:  # noqa: BLE001 - we want to report any parser failure
        return SourceDocument(doc_id=_doc_id(rel), file=rel, source_type=_type_for(path), status="failed",
                              error=f"{type(exc).__name__}: {exc}", market=market, language=language)


def _type_for(path: Path) -> str:
    return {".html": "html", ".htm": "html", ".pdf": "pdf", ".md": "markdown", ".csv": "csv", ".json": "json_form"}.get(
        path.suffix.lower(), "text")
