"""Knowledge-grounded voice agent used by Q1 (India) and Q3 (PH / ID).

Facts come from the Question 2 retriever. The system prompt holds persona,
disclosures, and conversation policy — not FAQs, premiums, or objection scripts.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from shared.config import TRANSCRIPTS_DIR, settings
from shared.llm import chat_json
from shared.pii import mask_text

from q2_knowledge_base.retriever import get_retriever

from . import crm
from .locale import INDIA, Locale
from .qualification import qualify

log = logging.getLogger(__name__)

SLOT_KEYS = ("name", "age", "city", "members", "conditions", "sum_insured", "occupation", "phone", "callback_time")


def _contains_any(text: str, phrases: List[str]) -> bool:
    t = text.lower()
    return any(p.lower() in t for p in phrases)


def extract_slots_regex(text: str) -> Dict[str, str]:
    """Offline slot filler so test calls still work without an LLM key."""
    out: Dict[str, str] = {}
    t = text.strip()
    m = re.search(r"\b(?:my name is|nama saya|ako si|this is|i am|i'm|name is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", t, re.I)
    if m:
        out["name"] = m.group(1).strip()
    m = re.search(r"\b(?:i(?:'| a)?m|age(?: is)?|umur(?: saya)?|edad(?: ko)?)\s*(\d{2})\b", t, re.I)
    if not m:
        m = re.search(r"\b(\d{2})\s*(?:years?|yrs?|yo|tahun)\b", t, re.I)
    if m:
        out["age"] = m.group(1)
    m = re.search(r"\b(?:in|from|live in|living in|based in|sa|di)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)", t, re.I)
    if m:
        c = re.sub(r"\bcity\b", "", m.group(1), flags=re.I).strip()
        if c.lower() not in {"the", "a", "my", "this", "our"} and c:
            out["city"] = c.title()
    if re.search(r"\b(wife|husband|spouse|child|children|son|daughter|kids|family|asawa|anak|istri|suami)\b", t, re.I):
        out["members"] = t
    if re.search(r"\b(diabet|hypertens|blood pressure|\bbp\b|asthma|thyroid|cancer|smok|tobacco|insulin)\b", t, re.I):
        out["conditions"] = t
    elif re.search(r"\b(no (health )?issue|healthy|none|nothing|fit|wala naman|tidak ada)\b", t, re.I):
        out["conditions"] = "none"
    m = re.search(r"\b(\d+)\s*lakh", t, re.I)
    if m:
        out["sum_insured"] = m.group(0)
    m = re.search(
        r"\b((?:call me back|callback|call you back|tawag|hubungi).{0,40})", t, re.I
    )
    if m:
        out["callback_time"] = m.group(1).strip()
    # conflicting age vs DOB year
    dob = re.search(r"\b(?:born|dob|date of birth).*?(19|20)(\d{2})\b", t, re.I)
    if dob and "age" in out:
        year = int(dob.group(1) + dob.group(2))
        implied = datetime.now().year - year
        if abs(implied - int(out["age"])) >= 3:
            out["age_conflict"] = f"stated age {out['age']} vs DOB year {year} (~{implied})"
    return out


@dataclass
class Turn:
    role: str
    text: str
    citations: List[str] = field(default_factory=list)
    confidence: Optional[float] = None
    action: Optional[str] = None


@dataclass
class CallSession:
    call_id: str
    locale: str
    started_at: str
    turns: List[Turn] = field(default_factory=list)
    slots: Dict[str, Any] = field(default_factory=dict)
    qualification: Dict[str, Any] = field(default_factory=dict)
    lead_id: Optional[str] = None
    ended: bool = False
    end_reason: Optional[str] = None
    disclosures_done: bool = True  # greeting already contains them

    def transcript_text(self) -> str:
        lines = []
        for t in self.turns:
            who = "AGENT" if t.role == "agent" else "CUSTOMER"
            lines.append(f"{who}: {t.text}")
        return "\n".join(lines)

    def public(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id, "locale": self.locale, "started_at": self.started_at,
            "slots": self.slots, "qualification": self.qualification, "lead_id": self.lead_id,
            "ended": self.ended, "end_reason": self.end_reason,
            "turns": [asdict(t) for t in self.turns],
        }


class GroundedVoiceAgent:
    def __init__(self, locale: Locale = INDIA):
        self.locale = locale
        self.retriever = get_retriever()
        self.sessions: Dict[str, CallSession] = {}

    def start(self) -> CallSession:
        sid = "C-" + uuid4().hex[:8].upper()
        sess = CallSession(call_id=sid, locale=self.locale.id, started_at=datetime.now().isoformat(timespec="seconds"))
        sess.turns.append(Turn("agent", self.locale.greeting))
        self.sessions[sid] = sess
        try:
            from q4_live_nudges.bridge import attach, feed
            attach(sid, asr_language=self.locale.asr_language,
                   vocabulary_prompt=self.locale.vocabulary_prompt)
            feed(sid, "agent", self.locale.greeting)
        except Exception:  # noqa: BLE001 — Q4 is optional if the package is missing
            log.debug("Q4 live pipeline not attached", exc_info=True)
        return sess

    def get(self, call_id: str) -> CallSession:
        return self.sessions[call_id]

    def turn(self, call_id: str, user_text: str) -> Dict[str, Any]:
        sess = self.sessions[call_id]
        user_text = (user_text or "").strip()
        if not user_text:
            return self._pack(sess, Turn("agent", "I did not catch that. Could you say that again?"))
        sess.turns.append(Turn("customer", user_text))
        low = user_text.lower()

        if _contains_any(low, self.locale.dnc_phrases):
            sess.ended = True
            sess.end_reason = "dnc"
            lead = self._save_lead(sess, status="DNC")
            return self._pack(sess, Turn("agent", self.locale.dnc_ack, action="mark_dnc"), extra={"lead": lead})

        if _contains_any(low, self.locale.escalation_phrases):
            sess.ended = True
            sess.end_reason = "escalated"
            sess.slots.update(extract_slots_regex(user_text))
            lead = self._save_lead(sess, status="Escalated")
            crm.post_escalation({"call_id": sess.call_id, "reason": "customer_requested_human", "slots": sess.slots})
            return self._pack(sess, Turn("agent", self.locale.escalate_ack, action="escalate"), extra={"lead": lead})

        sess.slots.update(extract_slots_regex(user_text))
        retrieval = self.retriever.search(user_text, k=4, market=self.locale.market)
        sess.qualification = qualify(sess.slots, market=self.locale.market).as_dict()

        reply, citations, action = self._compose(sess, user_text, retrieval)
        agent_turn = Turn("agent", reply, citations=citations, confidence=retrieval.confidence, action=action)
        extra: Dict[str, Any] = {
            "retrieval": {
                "confidence": retrieval.confidence, "tier": retrieval.tier, "grounded": retrieval.grounded,
                "hits": [{"id": h.record.record_id, "title": h.record.title, "citation": h.record.citation()}
                         for h in retrieval.hits[:4]],
            },
            "qualification": sess.qualification,
        }
        if action in {"create_lead", "schedule_callback"}:
            extra["lead"] = self._save_lead(sess, status=sess.qualification.get("status") or "Qualified")
        if action == "end":
            sess.ended = True
            sess.end_reason = "completed"
        return self._pack(sess, agent_turn, extra=extra)

    def save_transcript(self, call_id: str) -> str:
        sess = self.sessions[call_id]
        path = TRANSCRIPTS_DIR / f"{sess.locale}_{sess.call_id}.json"
        masked, _ = mask_text(json.dumps(sess.public(), ensure_ascii=False))
        path.write_text(masked, encoding="utf-8")
        txt = TRANSCRIPTS_DIR / f"{sess.locale}_{sess.call_id}.txt"
        txt.write_text(sess.transcript_text(), encoding="utf-8")
        return str(path)

    # ----- internals
    def _compose(self, sess: CallSession, user_text: str, retrieval) -> tuple:
        loc = self.locale
        if retrieval.tier == "low":
            # still continue qualification if they were filling a slot, not asking a fact
            filling = bool(extract_slots_regex(user_text)) and not user_text.strip().endswith("?")
            if not filling and self._looks_like_question(user_text):
                return loc.unavailable, [], None

        if settings.has_llm:
            return self._llm_compose(sess, user_text, retrieval)

        return self._template_compose(sess, user_text, retrieval)

    def _looks_like_question(self, text: str) -> bool:
        t = text.strip().lower()
        if t.endswith("?"):
            return True
        return bool(re.match(
            r"^(what|how|can|is|do|does|who|when|why|will|are|magkano|ano|pwede|boleh|berapa|apakah)\b", t
        ))

    def _llm_compose(self, sess, user_text, retrieval) -> tuple:
        loc = self.locale
        ctx = retrieval.context_block(4) if retrieval.tier != "low" else "(no reliable knowledge-base match)"
        sys = (
            f"{loc.system_addendum}\n\n"
            "GROUNDING RULES:\n"
            "- Answer product / policy / premium / objection questions ONLY from <<record_id>> context below.\n"
            "- If the context does not contain the answer, set unavailable=true and use the unavailable script.\n"
            "- Never invent numbers, waiting periods, or settlement ratios.\n"
            "- Ask at most ONE qualifying question per turn (name, age, city, members, health conditions).\n"
            "- When enough slots exist, summarise the deterministic qualification JSON you are given; do not override it.\n"
            "- Reply as spoken voice: no markdown, no bullet dump, no record_ids in the spoken text.\n\n"
            f"UNAVAILABLE SCRIPT: {loc.unavailable}\n"
            f"CURRENT SLOTS: {json.dumps(sess.slots)}\n"
            f"QUALIFICATION: {json.dumps(sess.qualification)}\n"
            f"KB CONTEXT:\n{ctx}\n"
        )
        history = []
        for t in sess.turns[-8:]:
            history.append({"role": "assistant" if t.role == "agent" else "user", "content": t.text})
        data = chat_json(
            [{"role": "system", "content": sys +
              ' Return JSON {"reply": str, "unavailable": bool, "citation_ids": [str], '
              '"action": null|"create_lead"|"schedule_callback"|"end", "slot_updates": {}}'}]
            + history,
            temperature=0.3,
            max_tokens=350,
        )
        if data.get("_fallback") or not (data.get("reply") or "").strip():
            return self._template_compose(sess, user_text, retrieval)
        reply = (data.get("reply") or "").strip() or loc.unavailable
        if data.get("unavailable") or retrieval.tier == "low" and self._looks_like_question(user_text):
            reply = loc.unavailable
        sess.slots.update(data.get("slot_updates") or {})
        cites = []
        wanted = set(data.get("citation_ids") or [])
        for h in retrieval.hits:
            if not wanted or h.record.record_id in wanted:
                cites.append(h.record.citation())
        action = data.get("action")
        if sess.qualification.get("status") in {"Qualified", "Referred", "Not Eligible"} and not action:
            if sess.slots.get("name") and sess.slots.get("age") and "create" not in (action or ""):
                # offer lead once qualification is known
                pass
        return reply, cites[:4], action

    def _template_compose(self, sess, user_text, retrieval) -> tuple:
        """Deterministic fallback used when OPENAI_API_KEY is missing."""
        loc = self.locale
        cites = [h.record.citation() for h in retrieval.hits[:3]] if retrieval.tier != "low" else []
        qn = self._looks_like_question(user_text) or _contains_any(
            user_text.lower(), ["expensive", "employer", "reject", "waiting", "object"]
        )
        if qn and retrieval.tier == "low":
            return loc.unavailable, [], None
        if qn and retrieval.hits:
            chunk = retrieval.hits[0].record.content
            spoken = chunk.split("Approved response:")[-1] if "Approved response:" in chunk else chunk
            spoken = re.sub(r"\s+", " ", spoken).strip()
            if len(spoken) > 420:
                spoken = spoken[:420].rsplit(" ", 1)[0] + "."
            ask = self._next_question(sess)
            return (spoken + (" " + ask if ask else "")), cites, None

        ask = self._next_question(sess)
        status = sess.qualification.get("status")
        wants_cb = bool(sess.slots.get("callback_time")) or bool(
            re.search(r"call me back|callback|send me a summary|pakicall|hubungi aku", user_text, re.I)
        )
        if wants_cb and sess.slots.get("name"):
            when = sess.slots.get("callback_time") or "a time you prefer"
            disc = " ".join(sess.qualification.get("disclaimers") or [])
            reply = (
                f"I will schedule a callback ({when}) and save a lead summary for a licensed advisor. {disc}"
            )
            return reply.strip(), cites, "schedule_callback"
        if status in {"Qualified", "Referred", "Not Eligible"} and not ask:
            plan = sess.qualification.get("plan") or "a suitable plan"
            reasons = "; ".join(sess.qualification.get("reasons") or [])
            disc = " ".join(sess.qualification.get("disclaimers") or [])
            reply = (
                f"Based on what you have shared, preliminary status is {status} for {plan}. {reasons}. {disc} "
                "I can create a lead and arrange a callback with a licensed advisor. What time works for you?"
            )
            return reply, cites, "create_lead"
        if ask:
            return ask, cites, None
        return loc.closing, cites, "end"

    def _next_question(self, sess: CallSession) -> Optional[str]:
        s = sess.slots
        if self.locale.id == "PH":
            order = [
                ("name", "Pangalan po ninyo?"),
                ("age", "Ilang taon po kayo?"),
                ("city", "Saang lungsod po kayo based?"),
                ("members", "Kasama po ba ang asawa o anak sa cover?"),
                ("conditions", "May health condition po ba na nade-declare, like diabetes or BP?"),
            ]
        elif self.locale.id == "ID":
            order = [
                ("name", "Siapa nama Bapak/Ibu?"),
                ("age", "Usia berapa tahun?"),
                ("city", "Tinggalnya di kota mana?"),
                ("members", "Pembiayaan untuk sendiri atau ada kendaraan kedua / pasangan?"),
                ("conditions", "Ada keterangan khusus — misalnya cicilan yang tertunda?"),
            ]
        else:
            order = [
                ("name", "May I have your full name?"),
                ("age", "What is your age?"),
                ("city", "Which city are you based in?"),
                ("members", "Who would you like to cover — just yourself, or spouse and children as well?"),
                ("conditions", "Any declared health conditions I should note, such as diabetes or blood pressure?"),
            ]
        for key, q in order:
            if not s.get(key):
                return q
        return None

    def _save_lead(self, sess: CallSession, status: str) -> Dict[str, Any]:
        rec = crm.create_lead({
            "call_id": sess.call_id, "market": sess.locale, "status": status,
            "slots": sess.slots, "qualification": sess.qualification,
            "end_reason": sess.end_reason,
        })
        sess.lead_id = rec["lead_id"]
        return rec

    def _pack(self, sess: CallSession, agent_turn: Turn, extra: Optional[Dict] = None) -> Dict[str, Any]:
        sess.turns.append(agent_turn)
        nudges: List[dict] = []
        try:
            from q4_live_nudges.bridge import feed, snapshot
            if len(sess.turns) >= 2 and sess.turns[-2].role == "customer":
                feed(sess.call_id, "customer", sess.turns[-2].text)
            feed(sess.call_id, "agent", agent_turn.text)
            snap = snapshot(sess.call_id)
            nudges = snap.get("nudges") or []
        except Exception:  # noqa: BLE001
            log.debug("Q4 feed skipped", exc_info=True)
        payload = {
            "call_id": sess.call_id,
            "reply": agent_turn.text,
            "citations": agent_turn.citations,
            "confidence": agent_turn.confidence,
            "action": agent_turn.action,
            "ended": sess.ended,
            "slots": sess.slots,
            "qualification": sess.qualification,
            "lead_id": sess.lead_id,
            "nudges": nudges[-5:],
        }
        if extra:
            payload.update(extra)
        return payload


_agents: Dict[str, GroundedVoiceAgent] = {}


def get_agent(locale_id: str = "IN") -> GroundedVoiceAgent:
    from .locale import LOCALES
    if locale_id not in _agents:
        loc = LOCALES.get(locale_id, INDIA)
        _agents[locale_id] = GroundedVoiceAgent(loc)
    return _agents[locale_id]
