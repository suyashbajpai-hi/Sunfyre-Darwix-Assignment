# Q2 — Production-ready knowledge base

This knowledge base is the **source of truth** for the Question 1 voice agent (and the Q3 locale bots). Product facts, waiting periods, premiums, objections, and compliance rules are **not** hardcoded in the agent prompt.

## Domain

Fictional insurer **Sentinel Health Insurance Company Ltd.** (India), created for this assessment so the corpus can include messy real-world inputs without copying a live insurer’s documents.

Use case served: **health-insurance lead qualification** (one of the five options in the assessment PDF).

## Input mix (as required)

| Type | Path | Why it is here |
|---|---|---|
| Web pages | `q2_knowledge_base/sources/website/*.html` | Nav, header, footer, cookie banner, duplicated legal footer |
| Product / marketing | `plans.html`, `marketing_brochure_2023.txt` | Brochure is an older edition (8,900 hospitals vs 9,500) |
| Policy / qualification | `underwriting_rules.md`, `policy_wording_family_shield.pdf` | Rules + an outdated line left in on purpose |
| Forms | `forms/proposal_form.json` | Field-name synonyms to standardise |
| Tables | `plan_rates.csv` | Includes a zero-premium placeholder row |
| PDF failure | `docs/corrupted_scan.pdf` | Pipeline must report `status=failed`, not crash |
| Duplicates | 2023 brochure vs 2024 website | Near-duplicate + superseded edition |
| Inconsistent terms | copay / co-pay / co-payment, PED, lakh/lac | Normaliser maps to canonical forms |
| PII | `customer_service_log.txt` | Phones, emails, names, policy numbers, Aadhaar — masked before indexing |

Website extraction is the same logic a crawler would use: BeautifulSoup, drop `nav`/`header`/`footer`/`aside`/cookie banners, walk headings into a heading path. See `q2_knowledge_base/ingest/loaders.py`.

## Schema

See `q2_knowledge_base/schema.py`. Every retrievable unit is a `KBRecord`:

- `record_id` — stable, e.g. `kb_in_product_015`
- `title` — heading path (`Plans > Sentinel Family Shield`)
- `content` — chunk text (PII already replaced with `[PHONE]`, `[EMAIL]`, …)
- `category` / `products` / `intent_types` / `tags`
- `source` — file, type, locator (heading or PDF page), doc version, doc date
- `version` / `kb_version` / `content_hash`
- `pii` / `pii_types`
- `superseded` — older/duplicate chunks kept for audit, excluded from retrieval
- `quality_flags` — `older_edition`, `zero_premium_value`, conflicts, …

Citation format: `[record_id | title | file § locator | vversion]`.

## Chunking

Heading-aware, not a blind 512-token window:

- One section (heading + body) is the default unit — the size a voice agent can actually speak.
- Long prose splits on sentences (~140 words, one-sentence overlap).
- FAQ Q+A never split.
- Tables split by rows, heading kept on every chunk.

## Taxonomy

Rule-based (deterministic, auditable) classifier in `ingest/taxonomy.py`. Categories: product, premium_pricing, policy_terms, waiting_periods, exclusions, claims, eligibility_underwriting, qualification_rules, objection_handling, compliance, faq, partnership, forms, customer_service, company.

Intent labels used by the voice agent: `product`, `policy`, `qualification`, `faq`, `objection`, `compliance`.

## Embedding / indexing / ranking

- **Sparse:** BM25 over title+content (title duplicated once).
- **Dense:** OpenAI `text-embedding-3-small` when `OPENAI_API_KEY` is set; otherwise BM25-only (repo still runs).
- **Fusion:** `0.5 * bm25_norm + 0.5 * cosine`, plus product-name and FAQ boosts.
- **Grounding confidence** is absolute (term coverage + BM25 strength + cosine), not “best of a bad list”. Below 0.30 the agent must refuse; 0.30–0.55 is a verify-or-refuse gate.

## Versioning

- `kb_version` = `YYYY.MM.DD-N` (N increments when the content-hash set changes).
- Per-record `version` bumps when the same `record_id` gets a new `content_hash`.
- Source file SHA-12 is stored in `data/kb/manifest.json`.

## Retrieval tests

`python -m q2_knowledge_base.retrieval_tests` — product, policy, qualification, FAQ, objection, compliance, and out-of-scope queries. Results: `docs/q2_retrieval_tests.md`.

## Rebuild

```bash
python -m q2_knowledge_base.pipeline --no-embed   # BM25 only
python -m q2_knowledge_base.pipeline              # + dense vectors (needs OPENAI_API_KEY)
```
