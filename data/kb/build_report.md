# Knowledge Base Build Report - 2026.10.01-3

Built at 2026-10-01T23:33:50

## Documents

| Source | Type | Market | Status | Sections | Raw chars | Clean chars | Version | Date | Flags |
|---|---|---|---|---|---|---|---|---|---|
| docs/compliance_disclosures.md | markdown | IN | ok | 5 | 2470 | 2296 | 1.4 | 2024-03-01 |  |
| docs/corrupted_scan.pdf | pdf | IN | failed - PdfStreamError: Stream has ended unexpectedly | 0 | 0 | 0 | 1.0 |  |  |
| docs/customer_service_log.txt | text | IN | ok | 7 | 2588 | 2475 | 1.0 | 2024-01-01 |  |
| docs/marketing_brochure_2023.txt | text | IN | ok | 11 | 2113 | 1967 | 1.0 | 2023-10-01 | older_edition |
| docs/objection_handling_playbook.md | markdown | IN | ok | 11 | 4128 | 3530 | 2024.1 | 2024-02-15 |  |
| docs/plan_rates.csv | csv | IN | ok | 3 | 1217 | 3044 | 1.0 |  |  |
| docs/policy_wording_family_shield.pdf | pdf | IN | ok | 24 | 6444 | 6272 | 1.2 | 2024-04-01 |  |
| docs/underwriting_rules.md | markdown | IN | ok | 8 | 3793 | 3674 | 3.2 | 2024-04-01 | contains_outdated_text |
| forms/proposal_form.json | json_form | IN | ok | 5 | 3959 | 2310 | April 2024 |  |  |
| website/faq.html | html | IN | ok | 16 | 6749 | 4382 | 1.0 |  |  |
| website/index.html | html | IN | ok | 4 | 4415 | 1817 | 1.0 |  |  |
| website/partners.html | html | IN | ok | 5 | 2626 | 1021 | 1.0 |  |  |
| website/plans.html | html | IN | ok | 6 | 5272 | 3284 | 1.0 | 2024-04-01 |  |
| objections_faq.md | markdown | PH | ok | 8 | 1961 | 1613 | 1.0 |  |  |
| products.md | markdown | PH | ok | 5 | 2114 | 1932 | 2.1 | 2024-06-01 |  |
| qualification.md | markdown | PH | ok | 5 | 1259 | 1092 | 1.3 | 2024-05-20 |  |
| keberatan_faq.md | markdown | ID | ok | 8 | 1602 | 1320 | 1.0 |  |  |
| kepatuhan.md | markdown | ID | ok | 4 | 692 | 590 | 1.0 | 2024-04-12 |  |
| produk.md | markdown | ID | ok | 7 | 2008 | 1765 | 1.0 |  |  |

## Cleaning

- boilerplate_lines_removed: 8
- repeated_lines_removed: 1
- repeated_patterns_detected: 1

## De-duplication

- exact_duplicates: 0
- near_duplicates: 2

Superseded chunks (kept for traceability, excluded from retrieval):

- `kb_in_product_001` (docs/marketing_brochure_2023.txt) - older edition
- `kb_in_product_002` (docs/marketing_brochure_2023.txt) - older edition
- `kb_in_claims_001` (docs/marketing_brochure_2023.txt) - near_duplicate_of:kb_in_claims_007 (jaccard=0.74)
- `kb_in_product_003` (docs/marketing_brochure_2023.txt) - near_duplicate_of:kb_in_product_016 (jaccard=0.56)
- `kb_in_product_004` (docs/marketing_brochure_2023.txt) - older edition
- `kb_in_product_005` (docs/marketing_brochure_2023.txt) - older edition
- `kb_in_product_006` (docs/marketing_brochure_2023.txt) - older edition
- `kb_in_waiting_periods_001` (docs/marketing_brochure_2023.txt) - older edition
- `kb_in_product_007` (docs/marketing_brochure_2023.txt) - older edition
- `kb_in_product_008` (docs/marketing_brochure_2023.txt) - older edition
- `kb_in_product_009` (docs/marketing_brochure_2023.txt) - older edition

## PII protection

Records with PII masked: 9

- EMAIL: 5 occurrences
- NAME: 3 occurrences
- PHONE: 8 occurrences
- POLICY_NO: 5 occurrences
- AADHAAR: 1 occurrences

## Source errors / conflicts flagged

- **zero_premium_value**: kb_in_premium_pricing_003
- **placeholder_value**: kb_in_premium_pricing_003
- **explicit_outdated_statement**: kb_in_eligibility_underwriting_003
- **conflict:network_hospitals**: 8,900 in kb_in_claims_001, kb_in_product_003; 9,500 in kb_in_claims_007, kb_in_product_016
- **conflict:claim_tat_days**: 5 in kb_in_claims_001; 4 in kb_in_claims_007
- **conflict:members**: 1.1 in kb_in_claims_001; 1.2 in kb_in_claims_007

## Records by category

- claims: 6
- company: 4
- compliance: 6
- customer_service: 7
- eligibility_underwriting: 10
- exclusions: 13
- faq: 16
- forms: 5
- objection_handling: 19
- partnership: 5
- policy_terms: 6
- premium_pricing: 12
- product: 16
- qualification_rules: 3
- waiting_periods: 3

## Records by market

- IN: 94
- PH: 18
- ID: 19

Embedding model: none (BM25 only)
