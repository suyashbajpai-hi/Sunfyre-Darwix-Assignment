"""Product / policy taxonomy and rule-based classification.

Categories (one per record) and intent_types (multi-label, used by the voice
agent to route "product / policy / qualification / FAQ / objection" questions):

  company                 - about us, licence, hospital network, settlement ratio
  product                 - plan descriptions, features, riders
  premium_pricing         - rate card, premium examples, payment modes, discounts
  policy_terms            - definitions, coverage clauses, renewal, free-look
  waiting_periods         - initial / PED / specific illness / maternity waits
  exclusions              - what is not covered
  claims                  - cashless / reimbursement process, documents, TAT
  eligibility_underwriting- entry age, medical tests, PED acceptance, loadings
  qualification_rules     - lead qualified / referred / not eligible logic
  objection_handling      - approved rebuttals
  compliance              - mandatory disclosures, prohibited statements
  faq                     - customer FAQ not falling in a stronger category
  partnership             - branch partner programme
  forms                   - proposal form fields
  customer_service        - service log learnings (PII-masked)

A small keyword scorer picks the category; the source file gives a prior.
This is deliberately deterministic (no LLM) so classification is reproducible
and auditable - an LLM classifier can be layered on top for ambiguous chunks.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

from ..schema import KBRecord

CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "waiting_periods": ["waiting period", "30 days", "36 months", "24 months", "12 months", "survival period", "initial waiting"],
    "exclusions": ["exclusion", "not covered", "excluded", "cosmetic", "infertility", "self-inflicted", "war", "experimental"],
    "claims": ["claim", "cashless", "reimbursement", "pre-authorisation", "discharge", "settle", "network hospital", "documents"],
    "eligibility_underwriting": ["entry age", "underwrit", "medical examination", "medical test", "bmi", "loading", "accept", "decline", "refer", "hba1c", "tobacco", "smoker", "ppme", "pre-policy"],
    "qualification_rules": ["lead", "qualified", "referred", "not eligible", "voice agent", "tele-sales", "capture"],
    "premium_pricing": ["premium", "rate", "gst", "discount", "pay monthly", "frequency", "annual premium", "cost", "price", "zone"],
    "objection_handling": ["objection", "approved response", "do not:", "reframe", "competitor", "discuss with my spouse"],
    "compliance": ["disclosure", "solicitation", "prohibited", "must not", "recorded for quality", "do-not-call", "rebating", "section 41"],
    "product": ["sum insured", "floater", "room rent", "restoration", "rider", "maternity", "add-on", "plan", "cover", "benefit", "feature"],
    "policy_terms": ["means", "definition", "grace period", "free look", "free-look", "renewal", "renewab", "cancellation", "nomination", "grievance", "portab"],
    "partnership": ["partner", "commission", "outlet", "posp", "corporate agent"],
    "forms": ["field ", "proposal form", "required)", "optional)"],
    "customer_service": ["ticket", "resolution:", "issue:"],
    "company": ["irdai", "licensed", "head office", "branches", "since 2011", "members", "settlement ratio", "about"],
    "faq": ["?"],
}

SOURCE_PRIORS: List[Tuple[re.Pattern, str, float]] = [
    (re.compile(r"underwriting_rules"), "eligibility_underwriting", 2.0),
    (re.compile(r"objection"), "objection_handling", 4.0),
    (re.compile(r"compliance"), "compliance", 4.0),
    (re.compile(r"plan_rates"), "premium_pricing", 4.0),
    (re.compile(r"proposal_form"), "forms", 5.0),
    (re.compile(r"customer_service"), "customer_service", 3.0),
    (re.compile(r"partners"), "partnership", 3.0),
    (re.compile(r"policy_wording"), "policy_terms", 1.5),
    (re.compile(r"faq"), "faq", 1.0),
    (re.compile(r"plans\.html|brochure"), "product", 1.5),
    (re.compile(r"index\.html"), "company", 1.5),
    (re.compile(r"shieldlife|bancassurance|philippines"), "product", 1.2),
    (re.compile(r"danacepat|mitradana|indonesia|cicilan"), "product", 1.2),
]

PRODUCT_PATTERNS: Dict[str, re.Pattern] = {
    "essential": re.compile(r"\bessential\b", re.I),
    "family_shield": re.compile(r"\bfamily shield\b", re.I),
    "senior_care": re.compile(r"\bsenior care\b", re.I),
    "critical_illness_rider": re.compile(r"\bcritical illness\b", re.I),
    "hospital_cash_rider": re.compile(r"\bhospital cash\b", re.I),
    "copay_waiver_rider": re.compile(r"\bco-payment waiver\b", re.I),
    "opd_rider": re.compile(r"\bOPD\b"),
    "shieldlife_term": re.compile(r"\bshieldlife term\b", re.I),
    "shieldlife_whole": re.compile(r"\bshieldlife whole\b", re.I),
    "credit_life": re.compile(r"\bcredit life\b", re.I),
    "dana_cepat": re.compile(r"\bdanacepat\b", re.I),
    "motor_plus": re.compile(r"\bmotorplus\b", re.I),
    "mobil_plus": re.compile(r"\bmobilplus\b", re.I),
}

INTENT_MAP: Dict[str, List[str]] = {
    "product": ["product"], "premium_pricing": ["product", "faq"], "policy_terms": ["policy"],
    "waiting_periods": ["policy", "faq"], "exclusions": ["policy"], "claims": ["policy", "faq"],
    "eligibility_underwriting": ["qualification"], "qualification_rules": ["qualification"],
    "objection_handling": ["objection"], "compliance": ["compliance"], "faq": ["faq"],
    "partnership": ["product"], "forms": ["qualification"], "customer_service": ["faq"], "company": ["product", "faq"],
}


def classify(rec: KBRecord) -> None:
    text = f"{rec.title}\n{rec.content}".lower()
    scores: Dict[str, float] = {c: 0.0 for c in CATEGORY_KEYWORDS}
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            n = text.count(kw)
            if n:
                scores[cat] += (1.0 + 0.3 * min(n - 1, 4)) * (2.0 if kw in rec.title.lower() else 1.0)
    for pat, cat, w in SOURCE_PRIORS:
        if pat.search(rec.source.file):
            scores[cat] += w
    scores["faq"] *= 0.4  # "?" is weak evidence
    best = max(scores.items(), key=lambda kv: kv[1])
    rec.category = best[0] if best[1] > 0 else "faq"
    second = sorted(scores.items(), key=lambda kv: -kv[1])[1]
    if second[1] >= 0.6 * best[1] and second[1] > 1:
        rec.subcategory = second[0]
    rec.products = [p for p, pat in PRODUCT_PATTERNS.items() if pat.search(rec.content) or pat.search(rec.title)]
    rec.intent_types = sorted(set(INTENT_MAP.get(rec.category, []) + (["faq"] if "faq" in rec.tags else [])))
