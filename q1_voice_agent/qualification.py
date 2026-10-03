"""Deterministic lead-qualification engine for Sentinel Health (Question 1).

Rules are taken from `q2_knowledge_base/sources/docs/underwriting_rules.md`.
The LLM never decides eligibility on its own — it reports this engine's output
and must still say "preliminary, subject to underwriting".
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

DECLINE_CONDITIONS = [
    "cancer", "chemotherapy", "malignant",
    "heart attack", "bypass", "angioplasty", "myocardial",
    "chronic kidney", "ckd", "dialysis",
]
REFER_CONDITIONS = [
    "insulin", "type 1", "type1", "complication", "retinopathy", "neuropathy", "nephropathy",
    "bmi", "obesity", "hazardous", "mining", "offshore", "stunt", "armed forces",
]
ACCEPT_WITH_LOADING = [
    "diabetes", "diabetic", "hypertension", "blood pressure", "bp", "asthma", "thyroid", "tobacco", "smok",
]
ZONE_A_CITIES = {
    "mumbai", "delhi", "noida", "gurgaon", "gurugram", "bengaluru", "bangalore", "chennai",
    "hyderabad", "kolkata", "pune", "ahmedabad", "navi mumbai", "thane", "faridabad", "ghaziabad",
}


@dataclass
class Qualification:
    status: str  # Incomplete | Qualified | Referred | Not Eligible
    plan: Optional[str] = None
    reasons: List[str] = field(default_factory=list)
    zone: Optional[str] = None
    ppme_required: bool = False
    disclaimers: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict:
        return {
            "status": self.status, "plan": self.plan, "reasons": self.reasons,
            "zone": self.zone, "ppme_required": self.ppme_required, "disclaimers": self.disclaimers,
        }


def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()


def _age(slots: Dict) -> Optional[int]:
    raw = slots.get("age")
    if raw is None or raw == "":
        return None
    try:
        return int(str(raw).strip())
    except ValueError:
        m = re.search(r"\d{1,3}", str(raw))
        return int(m.group()) if m else None


def _conditions(slots: Dict) -> str:
    c = slots.get("conditions") or slots.get("health") or ""
    if isinstance(c, list):
        c = ", ".join(c)
    return _norm(str(c))


def qualify(slots: Dict, market: str = "IN") -> Qualification:
    """slots: name, age, city, members, conditions, sum_insured, occupation, dob_age (optional conflict)."""
    if market == "PH":
        return _qualify_ph(slots)
    if market == "ID":
        return _qualify_id(slots)
    return _qualify_in(slots)


def _qualify_ph(slots: Dict) -> Qualification:
    missing = [k for k in ("name", "age") if not slots.get(k)]
    if missing:
        return Qualification("Incomplete", reasons=[f"still need: {', '.join(missing)}"])
    age = _age(slots)
    if age is None:
        return Qualification("Incomplete", reasons=["age is not a number"])
    q = Qualification("Qualified", plan="ShieldLife Term Protect")
    q.disclaimers.append("Indicative only. Final offer is the signed policy illustration from a licensed advisor.")
    if age < 18:
        q.status = "Not Eligible"
        q.reasons.append("minimum age 18 for new term / whole life")
        return q
    if age > 65:
        q.status = "Not Eligible"
        q.reasons.append("Term Protect new business is 18–65")
        return q
    blob = _norm(str(slots.get("members") or "") + " " + str(slots.get("conditions") or ""))
    if "credit life" in blob and "loan" not in blob and "banco isla" not in blob:
        q.status = "Not Eligible"
        q.plan = "Credit Life"
        q.reasons.append("credit life requires an existing Banco Isla loan")
        return q
    if 60 <= age <= 65:
        q.status = "Referred"
        q.reasons.append("age 60–65 wanting whole life is referred")
        return q
    q.reasons.append(f"age {age} inside term range; smoker/sum insured still needed for a quote")
    return q


def _qualify_id(slots: Dict) -> Qualification:
    missing = [k for k in ("name", "age") if not slots.get(k)]
    if missing:
        return Qualification("Incomplete", reasons=[f"still need: {', '.join(missing)}"])
    age = _age(slots)
    if age is None:
        return Qualification("Incomplete", reasons=["age is not a number"])
    q = Qualification("Qualified", plan="DanaCepat")
    q.disclaimers.append("Angka indikatif. Persetujuan final setelah survey cabang.")
    if age < 21 or age > 55:
        q.status = "Not Eligible"
        q.reasons.append("usia pemohon DanaCepat / MotorPlus 21–55")
        return q
    q.reasons.append(f"usia {age} masuk rentang; plafon/tenor dikonfirmasi petugas")
    return q


def _qualify_in(slots: Dict) -> Qualification:
    missing = [k for k in ("name", "age", "city") if not slots.get(k)]
    if missing:
        return Qualification("Incomplete", reasons=[f"still need: {', '.join(missing)}"])

    age = _age(slots)
    if age is None:
        return Qualification("Incomplete", reasons=["age is not a number"])

    cond = _conditions(slots)
    city = _norm(slots.get("city"))
    occupation = _norm(slots.get("occupation"))
    members = _norm(str(slots.get("members") or "self"))
    zone = "A" if any(z in city for z in ZONE_A_CITIES) else "B"

    # Conflicting details (e.g. stated age vs age implied by DOB)
    if slots.get("age_conflict"):
        return Qualification(
            "Referred", zone=zone,
            reasons=["stated age conflicts with date of birth — do not promise eligibility; clarify or refer"],
            disclaimers=["Eligibility is preliminary and subject to underwriting."],
        )

    q = Qualification("Qualified", zone=zone)
    q.disclaimers.append("Eligibility is preliminary and subject to underwriting; this is not an approval.")
    q.disclaimers.append("Any premium mentioned is indicative, exclusive of 18% GST, and subject to underwriting.")

    # Plan by age / family
    family = any(w in members for w in ("spouse", "wife", "husband", "child", "kids", "son", "daughter", "family", "2a"))
    if age < 18:
        q.status = "Not Eligible"
        q.reasons.append("entry age for adults is 18; children only as dependents on Family Shield (91 days–25 years)")
        return q
    if 61 <= age <= 80:
        q.plan = "Senior Care"
        q.ppme_required = True
        q.reasons.append("age 61–80 maps to Senior Care; pre-policy medical examination is compulsory")
    elif age > 80:
        q.status = "Not Eligible"
        q.plan = None
        q.reasons.append("Senior Care maximum entry age is 80; not eligible for a new policy")
        return q
    else:
        q.plan = "Family Shield" if family else "Essential"
        q.reasons.append(f"age {age} is inside 18–65; suggested plan {q.plan}")
        if age > 45:
            q.ppme_required = True
            q.reasons.append("age above 45: pre-policy medical examination required")

    blob = f"{cond} {occupation}"
    if any(k in blob for k in DECLINE_CONDITIONS):
        # heart attack: decline on Essential/Family Shield, refer on Senior Care
        if q.plan == "Senior Care" and any(k in blob for k in ("heart attack", "bypass", "angioplasty")):
            q.status = "Referred"
            q.reasons.append("cardiac history on Senior Care is referred to underwriting")
        else:
            q.status = "Not Eligible"
            q.reasons.append("declared condition is on the decline list (cancer / recent cardiac / CKD stage 3+)")
        return q
    if any(k in blob for k in REFER_CONDITIONS):
        q.status = "Referred"
        q.reasons.append("condition or occupation requires underwriter review")
        return q
    if any(k in blob for k in ACCEPT_WITH_LOADING) and cond not in {"", "none", "no", "nil", "healthy", "na"}:
        q.reasons.append("controlled declared condition is generally acceptable with loading and PED waiting period")
        if "diabet" in cond or "hypertens" in cond or "bp" in cond or "asthma" in cond or "thyroid" in cond:
            q.ppme_required = True

    si = str(slots.get("sum_insured") or "")
    if re.search(r"25\s*lakh|2500000", si.replace(",", "")):
        q.ppme_required = True
        q.reasons.append("sum insured Rs 25 lakh or more requires pre-policy medical examination")

    return q
