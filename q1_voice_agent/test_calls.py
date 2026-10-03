"""Scripted test calls for Question 1 required coverage.

    python -m q1_voice_agent.test_calls

Writes transcripts under data/transcripts/ and a results markdown under docs/.
Works without OPENAI_API_KEY (template replies + BM25 grounding).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from shared.config import ROOT_DIR, TRANSCRIPTS_DIR

from .agent import GroundedVoiceAgent
from .locale import INDIA

SCENARIOS = [
    {
        "id": "q1_cooperative",
        "title": "Cooperative customer",
        "lines": [
            "Hi, my name is Rohan Mehta.",
            "I am 34 years old, I live in Pune.",
            "I want to cover myself, my wife and one child.",
            "No health issues, we are all healthy.",
            "Family Shield with 10 lakh cover sounds right.",
            "Please create the lead and call me tomorrow at 6 pm.",
        ],
    },
    {
        "id": "q1_objection",
        "title": "Objection — too expensive / employer cover",
        "lines": [
            "This is Priya.",
            "I am 30, from Bengaluru.",
            "Just myself for now.",
            "It is too expensive, I already have cover from my employer.",
            "Okay, send me a summary and call me back Friday.",
        ],
    },
    {
        "id": "q1_conflicting",
        "title": "Incomplete then conflicting details",
        "lines": [
            "Hello.",
            "Name is Imran.",
            "I am 40 but my date of birth is 1978.",
            "I live in Delhi.",
            "Father is 82, can he buy a policy?",
        ],
    },
    {
        "id": "q1_oos",
        "title": "Out-of-scope question (must not invent)",
        "lines": [
            "Hi I am Neha, 29, from Chennai, just myself, no conditions.",
            "What is the stock price of Sentinel Health?",
            "Do you sell motor insurance?",
            "Who is your CEO?",
        ],
    },
    {
        "id": "q1_human",
        "title": "Human-assistance request",
        "lines": [
            "My name is Arjun, 45, Mumbai.",
            "I want to speak to a human advisor please, not a bot.",
        ],
    },
]


def run() -> dict:
    agent = GroundedVoiceAgent(INDIA)
    results = []
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    for sc in SCENARIOS:
        sess = agent.start()
        rows = [{"role": "agent", "text": sess.turns[0].text}]
        flags = {"unavailable": False, "escalated": False, "lead": False, "dnc": False}
        for line in sc["lines"]:
            out = agent.turn(sess.call_id, line)
            rows.append({"role": "customer", "text": line})
            rows.append({
                "role": "agent", "text": out["reply"], "citations": out.get("citations") or [],
                "confidence": out.get("confidence"), "action": out.get("action"),
            })
            if out.get("reply") == INDIA.unavailable or (out.get("retrieval") or {}).get("tier") == "low":
                flags["unavailable"] = True
            if out.get("action") == "escalate" or sess.end_reason == "escalated":
                flags["escalated"] = True
            if out.get("lead") or sess.lead_id:
                flags["lead"] = True
        rec = {
            "id": sc["id"], "title": sc["title"], "call_id": sess.call_id,
            "qualification": sess.qualification, "slots": sess.slots,
            "lead_id": sess.lead_id, "end_reason": sess.end_reason,
            "flags": flags, "turns": rows,
        }
        path = TRANSCRIPTS_DIR / f"{sc['id']}.json"
        rec["transcript_path"] = str(path)
        path.write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
        results.append(rec)

    summary = {
        "scenarios": len(results),
        "leads_created": sum(1 for r in results if r["lead_id"]),
        "escalations": sum(1 for r in results if r["end_reason"] == "escalated"),
        "unavailable_used": sum(1 for r in results if r["flags"]["unavailable"]),
    }
    _write_md(results, summary)
    return {"summary": summary, "results": results}


def _write_md(results: List[dict], summary: dict) -> None:
    docs = ROOT_DIR / "docs"
    docs.mkdir(exist_ok=True)
    lines = ["# Q1 — Test call transcripts and results", "",
             "Use case: **health-insurance lead qualification** for fictional Sentinel Health Insurance. "
             "The bot retrieves from the Question 2 knowledge base; FAQs and objections are not hardcoded.", "",
             f"Scenarios: {summary['scenarios']} · Leads: {summary['leads_created']} · "
             f"Escalations: {summary['escalations']} · Unavailable fallback used: {summary['unavailable_used']}", ""]
    for r in results:
        lines += [f"## {r['title']} (`{r['id']}`)", "",
                  f"- Call ID: `{r['call_id']}`  |  Lead: `{r['lead_id']}`  |  End: {r['end_reason']}",
                  f"- Slots: `{json.dumps(r['slots'], ensure_ascii=False)}`",
                  f"- Qualification: `{json.dumps(r['qualification'], ensure_ascii=False)}`",
                  f"- Transcript file: `{r['transcript_path']}`", "",
                  "| Who | Text | Grounding |", "|---|---|---|"]
        for t in r["turns"]:
            who = t["role"]
            cite = ""
            if t.get("citations"):
                cite = f"conf={t.get('confidence')}<br>" + "<br>".join(t["citations"][:2])
            elif t.get("action"):
                cite = t["action"]
            text = t["text"].replace("|", "/").replace("\n", " ")
            lines.append(f"| {who} | {text} | {cite} |")
        lines.append("")
    (docs / "q1_test_calls.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    out = run()
    print(json.dumps(out["summary"], indent=2))
    for r in out["results"]:
        print(f"{r['id']:<20} end={r['end_reason']!s:<12} lead={r['lead_id']} status={r['qualification'].get('status')}")
