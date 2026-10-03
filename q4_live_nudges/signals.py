"""Signal extraction for live calls (rules first, optional LLM confirmation).

Signals the assessment asks for:
  missed_opportunity / missed_cross_sell
  compliance_gap
  rising_frustration
  buying_signal
  callback_need
  topic_shift
  payment_difficulty
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from shared.config import settings
from shared.llm import chat_json


@dataclass
class Signal:
    kind: str
    confidence: float
    evidence: str
    t_end: float
    speaker: str = "customer"
    details: Dict = field(default_factory=dict)


CROSS_SELL = [
    re.compile(r"\b(second|another|other)\s+(car|vehicle|bike|motor|mobil|motor)\b", re.I),
    re.compile(r"\b(wife'?s? car|husband'?s? car|mobil (?:isteri|istri|suami)|motor dinas)\b", re.I),
    re.compile(r"\b(parents?|father|mother|asawa|anak|spouse|kids?)\b.{0,40}\b(cover|policy|insured)\b", re.I),
    re.compile(r"\bcritical illness\b", re.I),
]
BUYING = [
    re.compile(r"\b(how much|magkano|berapa|premium|quote|send (me )?the (summary|quote)|I'll take|let's proceed|sige po)\b", re.I),
]
FRUST = [
    re.compile(r"\b(this is ridiculous|useless|stupid bot|waste (of )?time|already told you|hindi niyo ba maintindihan|kesal|capek banget)\b", re.I),
    re.compile(r"\b(annoyed|frustrated|angry|fed up|irritat)\b", re.I),
    re.compile(r"!{2,}"),
]
PAYMENT = [
    re.compile(r"\b(cannot pay|can't pay|no money|gaji belum|dendanya|mahal banget|too expensive|hindi afford)\b", re.I),
]
CALLBACK = [
    re.compile(r"\b(call me back|callback|tawag(?:an)? (?:mo|ninyo)|hubungi (?:saya|aku)|not a good time)\b", re.I),
]
DISCLOSURE_MARKERS = [
    re.compile(r"this call is being recorded", re.I),
    re.compile(r"nire-record", re.I),
    re.compile(r"panggilan ini direkam", re.I),
    re.compile(r"subject matter of solicitation", re.I),
]
RISKY_AGENT = [
    re.compile(r"\b(guaranteed|100%\s*covered|no exclusions|approved|sure claim|no questions asked)\b", re.I),
    re.compile(r"\b(day one|from day 1).{0,20}(pre-existing|PED)\b", re.I),
]


def extract_rule_signals(text: str, speaker: str, t_end: float, agent_has_disclosed: bool) -> List[Signal]:
    out: List[Signal] = []
    if speaker == "customer":
        for rx in CROSS_SELL:
            if rx.search(text):
                out.append(Signal("missed_cross_sell", 0.82, text, t_end, speaker,
                                  {"nudge": "Customer mentioned another vehicle / family member. Offer the relevant multi-cover or rider before closing."}))
                break
        for rx in BUYING:
            if rx.search(text):
                out.append(Signal("buying_signal", 0.78, text, t_end, speaker,
                                  {"nudge": "Buying signal. Recap plan + disclaimer and offer to create the lead / illustration."}))
                break
        for rx in FRUST:
            if rx.search(text):
                out.append(Signal("rising_frustration", 0.88, text, t_end, speaker,
                                  {"nudge": "Acknowledge the frustration in one sentence before asking anything else. Offer a human."}))
                break
        for rx in PAYMENT:
            if rx.search(text):
                out.append(Signal("payment_difficulty", 0.8, text, t_end, speaker,
                                  {"nudge": "Offer an approved payment-support / lower SI / monthly mode / callback path. Do not invent a discount."}))
                break
        for rx in CALLBACK:
            if rx.search(text):
                out.append(Signal("callback_need", 0.75, text, t_end, speaker,
                                  {"nudge": "Stop pitching. Capture a callback slot and confirm it."}))
                break
    if speaker == "agent":
        if not agent_has_disclosed and t_end > 12 and not any(rx.search(text) for rx in DISCLOSURE_MARKERS):
            # evaluated at pipeline level using running window, not each line
            pass
        for rx in RISKY_AGENT:
            if rx.search(text):
                out.append(Signal("compliance_gap", 0.93, text, t_end, "agent",
                                  {"nudge": "Risky statement. Correct course: do NOT promise guaranteed cover. Restate underwriting disclaimer."}))
                break
    return out


def maybe_llm_signals(window: str, t_end: float) -> List[Signal]:
    if not settings.q4_use_llm_signals or not settings.has_llm:
        return []
    data = chat_json(
        [
            {"role": "system", "content": (
                "You monitor a live insurance/finance call. Return JSON "
                '{"signals":[{"kind": "missed_cross_sell|compliance_gap|rising_frustration|buying_signal|'
                'callback_need|payment_difficulty|none", "confidence": 0-1, "evidence": str, "nudge": str}]}. '
                "Only emit a signal if evidence is in the transcript. Prefer precision over recall. "
                "kind=none with empty list if the window is noisy or small talk."
            )},
            {"role": "user", "content": window[-2500:]},
        ],
        temperature=0.1,
        max_tokens=250,
    )
    out = []
    for s in data.get("signals") or []:
        kind = s.get("kind") or "none"
        if kind == "none":
            continue
        conf = float(s.get("confidence") or 0)
        out.append(Signal(kind, conf, s.get("evidence") or "", t_end, "mixed",
                          {"nudge": s.get("nudge") or "", "source": "llm"}))
    return out
