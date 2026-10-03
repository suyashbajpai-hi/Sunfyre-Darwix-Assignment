"""Retrieval test suite -> docs/q2_retrieval_tests.md + data/kb/retrieval_tests.json

Each case: user question, intent type, expected evidence (keywords that must be
present in the retrieved record) and optional expected source file. Verdict:

  correct           - top-1 record contains all expected keywords (or, for
                      out-of-scope cases, confidence tier is low/medium and no
                      hallucination risk)
  partially correct - expected evidence found in top-3 but not top-1
  incorrect         - evidence not in top-3 / out-of-scope query graded as high

    python -m q2_knowledge_base.retrieval_tests
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional

from shared.config import KB_DIR, ROOT_DIR

from .retriever import Retriever


@dataclass
class Case:
    question: str
    intent: str  # product | policy | qualification | faq | objection | compliance | out_of_scope
    expect_keywords: List[str] = field(default_factory=list)
    expect_source: Optional[str] = None
    market: str = "IN"
    expect_out_of_scope: bool = False


CASES: List[Case] = [
    Case("What is the difference between Family Shield and Essential?", "product",
         ["family shield", "essential"], "plans.html"),
    Case("Does Senior Care have a co-pay?", "product", ["senior care", "20%"]),
    Case("How much does Family Shield cost for two adults and one child?", "faq", ["18,900"]),
    Case("What is the waiting period for pre-existing diseases?", "policy", ["36 months"]),
    Case("What happens if I miss a premium payment?", "policy", ["grace period", "30 days"]),
    Case("Is maternity covered and after how long?", "policy", ["maternity", "24"]),
    Case("I have controlled type 2 diabetes, can I get a policy?", "qualification", ["diabetes", "36 months"]),
    Case("Can my father who is 82 years old buy a policy?", "qualification", ["61", "80"]),
    Case("Do I need a medical test if I am 50?", "qualification", ["45", "medical"]),
    Case("Customer says it is too expensive, how should I respond?", "objection", ["rs 20 a day"],
         "objection_handling_playbook.md"),
    Case("Customer already has insurance from employer", "objection", ["employer"],
         "objection_handling_playbook.md"),
    Case("Insurance companies always reject claims", "objection", ["96.4%"]),
    Case("Which disclosures are mandatory at the start of a sales call?", "compliance", ["recorded"],
         "compliance_disclosures.md"),
    Case("Can I port my existing policy from another insurer?", "faq", ["portab", "45 days"]),
    Case("Is cosmetic surgery covered?", "policy", ["cosmetic"]),
    Case("What is the stock price of Sentinel Health?", "out_of_scope", [], expect_out_of_scope=True),
    Case("Who is the CEO of Sentinel?", "out_of_scope", [], expect_out_of_scope=True),
    Case("Do you sell motor insurance?", "out_of_scope", [], expect_out_of_scope=True),
    Case("Magkano ang premium for ShieldLife Term Protect one million?", "product",
         ["1,150"], market="PH"),
    Case("What happens if the policy lapses in the Philippines?", "policy",
         ["31-day"], market="PH"),
    Case("Berapa denda keterlambatan cicilan MitraDana?", "policy",
         ["0,5%"], market="ID"),
    Case("Berapa DP MotorPlus bekas?", "product", ["20%"], market="ID"),
]


def run(cases: List[Case] = CASES, write: bool = True) -> dict:
    retriever = Retriever()
    results = []
    for c in cases:
        res = retriever.search(c.question, k=3, market=c.market)
        top = res.hits[0].record if res.hits else None
        verdict = "incorrect"
        reason = ""
        if c.expect_out_of_scope:
            if res.tier == "low":
                verdict, reason = "correct", "low confidence -> agent will say information is unavailable"
            elif res.tier == "medium":
                verdict, reason = "partially correct", "medium confidence -> LLM verification gate must reject"
            else:
                verdict, reason = "incorrect", "high confidence on out-of-scope query (hallucination risk)"
        else:
            def has_all(rec):
                t = f"{rec.title} {rec.content}".lower()
                src_ok = (c.expect_source is None) or c.expect_source in rec.source.file
                return all(k.lower() in t for k in c.expect_keywords) and src_ok

            if top and has_all(top):
                verdict, reason = "correct", "top-1 record contains expected evidence"
            elif any(has_all(h.record) for h in res.hits):
                verdict, reason = "partially correct", "evidence in top-3 but not ranked first"
            else:
                reason = "expected evidence not in top-3"
            if verdict == "correct" and res.tier != "high":
                verdict, reason = "partially correct", f"evidence found but confidence tier={res.tier}"
        results.append({
            "question": c.question, "intent": c.intent, "market": c.market,
            "retrieved_record": top.record_id if top else None,
            "retrieved_title": top.title if top else None,
            "retrieved_excerpt": (top.content[:220] + "...") if top else None,
            "source": f"{top.source.file} § {top.source.locator}" if top else None,
            "confidence": res.confidence, "tier": res.tier, "mode": res.mode,
            "relevance_explanation": res.hits[0].explanation if res.hits else "no hits",
            "verdict": verdict, "verdict_reason": reason,
            "top3": [h.record.record_id for h in res.hits],
        })

    summary = {
        "total": len(results),
        "correct": sum(r["verdict"] == "correct" for r in results),
        "partially_correct": sum(r["verdict"] == "partially correct" for r in results),
        "incorrect": sum(r["verdict"] == "incorrect" for r in results),
        "mode": results[0]["mode"] if results else "n/a",
    }
    out = {"summary": summary, "results": results}
    if write:
        (KB_DIR / "retrieval_tests.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        _write_md(out, ROOT_DIR / "docs" / "q2_retrieval_tests.md")
    return out


def _write_md(out: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    s = out["summary"]
    lines = ["# Q2 - Retrieval Test Results", "",
             f"Retrieval mode: **{s['mode']}** | Total: {s['total']} | Correct: {s['correct']} | "
             f"Partially correct: {s['partially_correct']} | Incorrect: {s['incorrect']}", "",
             "Verdict rules: *correct* = top-1 record contains the expected evidence with high grounding confidence; "
             "*partially correct* = evidence in top-3 or confidence tier medium; *incorrect* = evidence absent. "
             "For out-of-scope questions, *correct* means the system reports low confidence so the voice agent "
             "says the information is unavailable instead of inventing an answer.", ""]
    for i, r in enumerate(out["results"], start=1):
        lines += [f"## {i}. {r['question']}", "",
                  f"- **Intent type:** {r['intent']}  |  **Market:** {r['market']}",
                  f"- **Retrieved record:** `{r['retrieved_record']}` - {r['retrieved_title']}",
                  f"- **Source reference:** {r['source']}",
                  f"- **Excerpt:** {r['retrieved_excerpt']}",
                  f"- **Confidence:** {r['confidence']} (tier: {r['tier']})",
                  f"- **Relevance explanation:** {r['relevance_explanation']}",
                  f"- **Verdict:** **{r['verdict']}** - {r['verdict_reason']}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    out = run()
    print(json.dumps(out["summary"], indent=2))
    for r in out["results"]:
        print(f"{r['verdict']:<18} conf={r['confidence']:<6} {r['question']}  -> {r['retrieved_record']}")
