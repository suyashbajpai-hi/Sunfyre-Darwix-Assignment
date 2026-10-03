"""Text-to-speech.

Two providers:

* **Edge TTS** (default, free, no API key). Microsoft neural voices include
  genuinely native Filipino (`fil-PH-BlessicaNeural`, `fil-PH-AngeloNeural`)
  and Indonesian (`id-ID-GadisNeural`, `id-ID-ArdiNeural`) voices, which is
  what Question 3 asks for. Output is MP3.
* **OpenAI TTS** (`tts-1`). Multilingual but not a native accent for fil/id.
  It can output raw PCM, which we wrap into 16-bit WAV so that synthetic
  test calls can be mixed/chunked with the stdlib `wave` module (no ffmpeg
  dependency). Used for the English agent voice in WAV test-call synthesis
  for Question 4.

Compromise documented in docs/q3_localization.md: Edge TTS voices are native but
cannot be fine-tuned for regional Indonesian accents; prosody for Taglish is
good but occasional English words get Filipino phonology.
"""
from __future__ import annotations

import asyncio
import io
import logging
import struct
import time
from dataclasses import dataclass
from typing import Optional

from .config import settings
from .llm import get_client

log = logging.getLogger(__name__)

LANG_TO_EDGE_VOICE = {
    "en": lambda: settings.tts_voice_en,
    "fil": lambda: settings.tts_voice_fil,
    "tl": lambda: settings.tts_voice_fil,
    "id": lambda: settings.tts_voice_id,
}


@dataclass
class TTSResult:
    audio: bytes
    mime: str  # audio/mpeg or audio/wav
    voice: str
    latency_ms: float
    provider: str


def pcm16_to_wav(pcm: bytes, sample_rate: int = 24000, channels: int = 1) -> bytes:
    byte_rate = sample_rate * channels * 2
    header = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE"
    header += b"fmt " + struct.pack("<IHHIIHH", 16, 1, channels, sample_rate, byte_rate, channels * 2, 16)
    header += b"data" + struct.pack("<I", len(pcm))
    return header + pcm


async def _edge_tts_async(text: str, voice: str, rate: str = "+0%") -> bytes:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()


def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        # Called from inside an event loop (FastAPI) -> run in a worker thread
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(lambda: asyncio.run(coro)).result()
    return asyncio.run(coro)


def synthesize(text: str, lang: str = "en", *, voice: Optional[str] = None, provider: Optional[str] = None,
               rate: str = "+0%") -> TTSResult:
    """Synthesize speech. Returns MP3 for edge, WAV for openai."""
    provider = provider or settings.tts_provider
    t0 = time.perf_counter()
    text = text.strip()
    if not text:
        return TTSResult(audio=b"", mime="audio/mpeg", voice="", latency_ms=0.0, provider=provider)

    if provider == "edge":
        voice = voice or LANG_TO_EDGE_VOICE.get(lang, LANG_TO_EDGE_VOICE["en"])()
        try:
            audio = _run_async(_edge_tts_async(text, voice, rate=rate))
            return TTSResult(audio=audio, mime="audio/mpeg", voice=voice, latency_ms=(time.perf_counter() - t0) * 1000,
                             provider="edge")
        except Exception as exc:  # noqa: BLE001
            log.warning("Edge TTS failed (%s); falling back to OpenAI TTS", exc)
            provider = "openai"

    client = get_client()
    if client is None:
        return TTSResult(audio=b"", mime="audio/wav", voice="", latency_ms=0.0, provider="none")
    voice = voice if (voice and not voice.endswith("Neural")) else settings.openai_tts_voice
    resp = client.audio.speech.create(model=settings.openai_tts_model, voice=voice, input=text, response_format="pcm")
    wav = pcm16_to_wav(resp.content, 24000, 1)
    return TTSResult(audio=wav, mime="audio/wav", voice=voice, latency_ms=(time.perf_counter() - t0) * 1000,
                     provider="openai")


def synthesize_wav(text: str, voice: Optional[str] = None) -> bytes:
    """Always returns 24 kHz mono 16-bit WAV (OpenAI TTS). Used for test-call synthesis."""
    res = synthesize(text, "en", voice=voice, provider="openai")
    return res.audio
