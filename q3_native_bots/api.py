"""FastAPI routes for Q3 Philippines / Indonesia voice bots."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from q1_voice_agent.agent import get_agent
from q1_voice_agent.locale import LOCALES
from shared.asr import transcribe_bytes
from shared.tts import synthesize

router = APIRouter(prefix="/native", tags=["Q3 Native-language bots"])
_UI = Path(__file__).parent / "static" / "index.html"


class TextTurn(BaseModel):
    call_id: str
    text: str
    market: str = "PH"


@router.get("", response_class=HTMLResponse, include_in_schema=False)
def ui():
    return HTMLResponse(_UI.read_text(encoding="utf-8"),
                        headers={"Cache-Control": "no-store, no-cache, must-revalidate"})


@router.post("/start/{market}")
def start(market: str):
    market = market.upper()
    if market not in LOCALES:
        raise HTTPException(400, "market must be PH or ID (or IN)")
    loc = LOCALES[market]
    sess = get_agent(market).start()
    audio = synthesize(sess.turns[0].text, lang=loc.tts_lang)
    return {
        "call_id": sess.call_id, "reply": sess.turns[0].text, "locale": market,
        "asr_language": loc.asr_language, "tts_voice": audio.voice, "company": loc.company,
        "use_case": loc.use_case, "vocabulary_prompt": loc.vocabulary_prompt,
    }


@router.post("/turn-text")
def turn_text(body: TextTurn):
    market = body.market.upper()
    agent = get_agent(market)
    if body.call_id not in agent.sessions:
        raise HTTPException(404, "unknown call_id")
    loc = LOCALES[market]
    result = agent.turn(body.call_id, body.text)
    audio = synthesize(result["reply"], lang=loc.tts_lang)
    result["tts_voice"] = audio.voice
    result["market"] = market
    return result


@router.post("/turn-audio")
async def turn_audio(call_id: str = Form(...), market: str = Form("PH"), audio: UploadFile = File(...)):
    market = market.upper()
    loc = LOCALES[market]
    agent = get_agent(market)
    if call_id not in agent.sessions:
        raise HTTPException(404, "unknown call_id")
    raw = await audio.read()
    asr = transcribe_bytes(
        raw, filename=audio.filename or "clip.webm",
        language=loc.asr_language,  # None => auto, required for Taglish / colloquial ID
        vocabulary_prompt=loc.vocabulary_prompt,
    )
    if asr.fallback or not asr.text:
        msg = (
            "Hindi ko po nakuha ang audio." if market == "PH"
            else "Maaf, audio tidak bisa ditranskripsi."
        )
        sess = agent.sessions[call_id]
        return {
            "reply": msg,
            "asr_text": "",
            "ended": sess.ended,
            "call_id": call_id,
            "market": market,
            "slots": sess.slots,
            "qualification": sess.qualification,
            "lead_id": sess.lead_id,
        }
    result = agent.turn(call_id, asr.text)
    result.update({
        "asr_text": asr.text, "asr_latency_ms": asr.latency_ms, "asr_language": asr.language,
        "asr_config": {"forced_language": loc.asr_language, "vocabulary_prompt": loc.vocabulary_prompt},
    })
    tts = synthesize(result["reply"], lang=loc.tts_lang)
    result["tts_voice"] = tts.voice
    return result


@router.get("/tts")
def tts(text: str, lang: str = "fil"):
    audio = synthesize(text, lang=lang)
    return Response(content=audio.audio, media_type=audio.mime)
