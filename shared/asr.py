"""Speech-to-text wrapper.

Design notes
------------
* Provider: OpenAI Whisper (`whisper-1`). Whisper is multilingual and handles
  code-switching (Taglish, Bahasa + English loanwords) reasonably well when it
  is *not* forced to a single language. We therefore expose two knobs:
    - `language`: ISO-639-1 hint ("en", "tl", "id"). Pass None to auto-detect,
      which is what we use for code-switched markets.
    - `vocabulary_prompt`: domain glossary injected as Whisper's `prompt`
      (e.g. "cicilan, tenor, denda, jatuh tempo") which strongly biases
      recognition of finance terms and local words.
* Every call returns latency in ms so Q4 can report per-chunk ASR latency.
"""
from __future__ import annotations

import io
import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional

from .config import settings
from .llm import get_client

log = logging.getLogger(__name__)


@dataclass
class ASRResult:
    text: str
    language: Optional[str]
    latency_ms: float
    segments: List[dict] = field(default_factory=list)
    fallback: bool = False


def _transcribe_gemini(
    audio: bytes,
    filename: str,
    language: Optional[str] = None,
    vocabulary_prompt: Optional[str] = None,
) -> ASRResult:
    import base64
    import httpx

    t0 = time.perf_counter()
    mime = "audio/webm"
    fn = filename.lower()
    if fn.endswith(".wav"):
        mime = "audio/wav"
    elif fn.endswith(".mp4") or fn.endswith(".m4a"):
        mime = "audio/mp4"
    elif fn.endswith(".mp3"):
        mime = "audio/mp3"

    b64 = base64.b64encode(audio).decode("utf-8")
    prompt = "Transcribe this audio verbatim in the spoken language."
    if language:
        prompt += f" Language hint: {language}."
    if vocabulary_prompt:
        prompt += f" Domain vocabulary: {vocabulary_prompt}."
    prompt += " Output ONLY the plain transcribed words. Do not add quotes, commentary, or notes."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={settings.gemini_api_key}"
    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": mime, "data": b64}},
                {"text": prompt}
            ]
        }],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 400,
        }
    }
    try:
        resp = httpx.post(url, json=payload, timeout=25.0)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                text = parts[0].get("text", "").strip()
        latency = (time.perf_counter() - t0) * 1000.0
        return ASRResult(text=text, language=language, latency_ms=latency)
    except Exception as exc:
        log.error("Gemini ASR failed: %s", exc)
        return ASRResult(text="", language=language, latency_ms=(time.perf_counter() - t0) * 1000.0, fallback=True)


def transcribe_bytes(
    audio: bytes,
    filename: str = "audio.wav",
    *,
    language: Optional[str] = None,
    vocabulary_prompt: Optional[str] = None,
    verbose: bool = True,
) -> ASRResult:
    if settings.has_gemini and not settings.has_openai:
        return _transcribe_gemini(audio, filename, language=language, vocabulary_prompt=vocabulary_prompt)

    client = get_client()
    t0 = time.perf_counter()
    if client is None:
        return ASRResult(text="", language=language, latency_ms=0.0, fallback=True)

    buf = io.BytesIO(audio)
    buf.name = filename  # the SDK infers the container from the name
    kwargs = {"model": settings.asr_model, "file": buf}
    if language:
        kwargs["language"] = language
    if vocabulary_prompt:
        kwargs["prompt"] = vocabulary_prompt[:800]
    if verbose:
        kwargs["response_format"] = "verbose_json"

    try:
        resp = client.audio.transcriptions.create(**kwargs)
    except Exception as exc:  # noqa: BLE001
        log.error("ASR failed: %s", exc)
        return ASRResult(text="", language=language, latency_ms=(time.perf_counter() - t0) * 1000, fallback=True)

    latency = (time.perf_counter() - t0) * 1000.0
    text = (getattr(resp, "text", "") or "").strip()
    detected = getattr(resp, "language", None) or language
    segments = []
    for seg in getattr(resp, "segments", None) or []:
        segments.append(
            {
                "start": getattr(seg, "start", None),
                "end": getattr(seg, "end", None),
                "text": getattr(seg, "text", ""),
                "no_speech_prob": getattr(seg, "no_speech_prob", None),
                "avg_logprob": getattr(seg, "avg_logprob", None),
            }
        )
    return ASRResult(text=text, language=detected, latency_ms=latency, segments=segments)


def transcribe_file(path: str, **kw) -> ASRResult:
    with open(path, "rb") as fh:
        return transcribe_bytes(fh.read(), filename=path.split("/")[-1].split("\\")[-1], **kw)
