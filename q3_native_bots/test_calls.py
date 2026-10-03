"""Q3 scripted calls — at least two per market, covering required behaviours.

    python -m q3_native_bots.test_calls
"""
from __future__ import annotations

import json
from typing import List

from q1_voice_agent.agent import GroundedVoiceAgent
from q1_voice_agent.locale import INDONESIA, PHILIPPINES
from shared.config import ROOT_DIR, TRANSCRIPTS_DIR

PH_SCENARIOS = [
    {
        "id": "ph_cooperative_taglish",
        "title": "PH cooperative Taglish lead",
        "lines": [
            "Hello po, ako si Ana Reyes, 32, from Quezon City.",
            "Gusto ko sana term life, asawa ko ang beneficiary.",
            "Hindi po ako smoker. Magkano po ang premium for one million coverage?",
            "Sige po, pakicall back tomorrow evening.",
        ],
    },
    {
        "id": "ph_objection_lapse",
        "title": "PH objection + human escalation",
        "lines": [
            "This is Carlo, 40, Makati, smoker.",
            "Baka mag-lapse, sayang. May insurance na ako sa office.",
            "Gusto ko kausapin ang tao sa branch, please.",
        ],
    },
    {
        "id": "ph_codeswitch_creditlife",
        "title": "PH mixed English finance terms + out of scope",
        "lines": [
            "Hi I'm Bea, 28, Cebu. Wala akong loan sa Banco Isla.",
            "Pwede ba credit life? Also what is ShieldLife stock price?",
        ],
    },
]

ID_SCENARIOS = [
    {
        "id": "id_cooperative_formal",
        "title": "ID cooperative formal Bahasa",
        "lines": [
            "Selamat siang, nama saya Budi Santoso, usia 35, tinggal di Jakarta.",
            "Saya mau tanya DanaCepat, plafon 20 juta, tenor 12 bulan. Berapa angsurannya?",
            "Baik, silakan callback besok sore.",
        ],
    },
    {
        "id": "id_colloquial_denda",
        "title": "ID colloquial + denda objection + mixed loanwords",
        "lines": [
            "Halo Mbak, aku Rina, 29 tahun, di Bandung.",
            "Cicilannya telat, dendanya kejebak mahal banget dong. DP MotorPlus bisa diturunin?",
            "Ya udah, hubungi aku setelah gajian tanggal 10.",
        ],
    },
    {
        "id": "id_jawa_accent_escalation",
        "title": "ID Yogyakarta phrasing (regional) + human ask",
        "lines": [
            "Nggih Mbak, kula Pak Slamet, umur 47, Yogyakarta.",
            "Monggo dicek tenor MobilPlus kula, jatuh tempo kapan, angsuran berapa.",
            "Kula nyuwun ngomong kalih petugas cabang, nggih.",
        ],
    },
]


def _run_market(locale, scenarios) -> List[dict]:
    agent = GroundedVoiceAgent(locale)
    out = []
    for sc in scenarios:
        sess = agent.start()
        rows = [{"role": "agent", "text": sess.turns[0].text}]
        for line in sc["lines"]:
            r = agent.turn(sess.call_id, line)
            rows.append({"role": "customer", "text": line})
            rows.append({"role": "agent", "text": r["reply"], "citations": r.get("citations") or [],
                         "confidence": r.get("confidence"), "action": r.get("action")})
        rec = {
            "id": sc["id"], "title": sc["title"], "market": locale.market, "call_id": sess.call_id,
            "slots": sess.slots, "qualification": sess.qualification, "lead_id": sess.lead_id,
            "end_reason": sess.end_reason, "turns": rows,
        }
        path = TRANSCRIPTS_DIR / f"{sc['id']}.json"
        rec["transcript_path"] = str(path)
        path.write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
        out.append(rec)
    return out


def run() -> dict:
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    ph = _run_market(PHILIPPINES, PH_SCENARIOS)
    idn = _run_market(INDONESIA, ID_SCENARIOS)
    results = ph + idn
    _write_md(results)
    return {"ph": len(ph), "id": len(idn), "results": results}


def _write_md(results: List[dict]) -> None:
    lines = ["# Q3 — Native-language test calls", "",
             "Two markets, same grounded-agent core as Q1, **localized KB + locale pack** "
             "(not a translated India script). ASR is configured per market in `q1_voice_agent/locale.py`.", ""]
    for r in results:
        lines += [f"## {r['title']} (`{r['id']}` · {r['market']})", "",
                  f"- End: {r['end_reason']} · Lead: `{r['lead_id']}` · file `{r['transcript_path']}`", ""]
        for t in r["turns"]:
            prefix = "**Agent**" if t["role"] == "agent" else "**Customer**"
            extra = ""
            if t.get("citations"):
                extra = f"  \n  _{t['citations'][0]}_"
            lines.append(f"- {prefix}: {t['text']}{extra}")
        lines.append("")
    (ROOT_DIR / "docs" / "q3_test_calls.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    out = run()
    print(json.dumps({"ph": out["ph"], "id": out["id"]}, indent=2))
    for r in out["results"]:
        print(f"{r['id']:<32} {r['end_reason']}")
