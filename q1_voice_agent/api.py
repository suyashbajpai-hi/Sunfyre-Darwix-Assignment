"""FastAPI routes for the Q1 web calling interface."""
from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from shared.asr import transcribe_bytes
from shared.config import settings
from shared.tts import synthesize

from q4_live_nudges.bridge import snapshot

from .agent import get_agent
from .crm import list_leads
from .locale import INDIA

router = APIRouter(prefix="/agent", tags=["Q1 Voice Agent"])
_UI = Path(__file__).parent / "static" / "index.html"


class TextTurn(BaseModel):
    call_id: str
    text: str


@router.get("", response_class=HTMLResponse, include_in_schema=False)
def ui():
    html = _UI.read_text(encoding="utf-8")
    return HTMLResponse(html, headers={"Cache-Control": "no-store, no-cache, must-revalidate"})


@router.post("/start")
def start():
    agent = get_agent("IN")
    sess = agent.start()
    audio = synthesize(sess.turns[0].text, lang=INDIA.tts_lang)
    return {
        "call_id": sess.call_id,
        "reply": sess.turns[0].text,
        "locale": "IN",
        "tts_voice": audio.voice,
        "tts_mime": audio.mime,
        "nudges": (snapshot(sess.call_id).get("nudges") or [])[-5:],
        "whisper": settings.has_asr,
        "llm": settings.has_llm,
    }


@router.post("/turn-text")
def turn_text(body: TextTurn):
    agent = get_agent("IN")
    if body.call_id not in agent.sessions:
        raise HTTPException(404, "unknown call_id — POST /agent/start first")
    result = agent.turn(body.call_id, body.text)
    audio = synthesize(result["reply"], lang=INDIA.tts_lang)
    result["tts_voice"] = audio.voice
    result["tts_mime"] = audio.mime
    return result


@router.post("/turn-audio")
async def turn_audio(call_id: str = Form(...), audio: UploadFile = File(...)):
    agent = get_agent("IN")
    if call_id not in agent.sessions:
        raise HTTPException(404, "unknown call_id")
    raw = await audio.read()
    asr = transcribe_bytes(raw, filename=audio.filename or "clip.webm",
                           language=INDIA.asr_language, vocabulary_prompt=INDIA.vocabulary_prompt)
    if asr.fallback or not asr.text:
        sess = agent.sessions[call_id]
        msg = (
            "Could not transcribe that audio clip. Please check mic permissions "
            "and speak for a second or two after clicking Talk."
        )
        return {
            "reply": msg,
            "asr_text": "",
            "ended": sess.ended,
            "call_id": call_id,
            "slots": sess.slots,
            "qualification": sess.qualification,
            "lead_id": sess.lead_id,
        }
    result = agent.turn(call_id, asr.text)
    result["asr_text"] = asr.text
    result["asr_latency_ms"] = asr.latency_ms
    result["asr_language"] = asr.language
    tts = synthesize(result["reply"], lang=INDIA.tts_lang)
    result["tts_voice"] = tts.voice
    result["tts_mime"] = tts.mime
    return result


@router.get("/status")
def status():
    model = settings.asr_model if settings.has_openai else ("gemini-2.0-flash" if settings.has_gemini else "none")
    return {"whisper": settings.has_asr, "llm": settings.has_llm, "asr_model": model}


@router.get("/tts")
def tts(text: str, lang: str = "en"):
    audio = synthesize(text, lang=lang)
    return Response(content=audio.audio, media_type=audio.mime)


@router.get("/session/{call_id}")
def session(call_id: str):
    agent = get_agent("IN")
    if call_id not in agent.sessions:
        raise HTTPException(404, "unknown call_id")
    return agent.sessions[call_id].public()


@router.post("/session/{call_id}/save")
def save(call_id: str):
    agent = get_agent("IN")
    if call_id not in agent.sessions:
        raise HTTPException(404, "unknown call_id")
    return {"path": agent.save_transcript(call_id)}


@router.get("/leads")
def leads(limit: int = 30):
    return list_leads(limit)
