"""Attach a Q4 live-insight pipeline to a Q1/Q3 voice call.

The assessment allows recorded calls from Q1 or Q3 to be reused for Q4.
This module does it *during* the call: every agent/customer turn is ingested
as a timed chunk so nudges can appear before the call ends.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .controls import Nudge
from .pipeline import LiveInsightPipeline

_live: Dict[str, LiveInsightPipeline] = {}
_clock: Dict[str, float] = {}


def _dur(text: str, fallback: float = 4.0) -> float:
    words = max(1, len((text or "").split()))
    return max(2.0, min(14.0, words * 0.38)) if text else fallback


def attach(call_id: str, asr_language: Optional[str] = None,
           vocabulary_prompt: Optional[str] = None) -> LiveInsightPipeline:
    pipe = LiveInsightPipeline(call_id, asr_language=asr_language, vocabulary_prompt=vocabulary_prompt)
    _live[call_id] = pipe
    _clock[call_id] = 0.0
    return pipe


def feed(call_id: str, speaker: str, text: str) -> List[Nudge]:
    if not text:
        return []
    pipe = _live.get(call_id) or attach(call_id)
    t0 = _clock.get(call_id, 0.0)
    t1 = t0 + _dur(text)
    _clock[call_id] = t1
    role = "customer" if speaker in {"customer", "cust", "user"} else "agent"
    return pipe.ingest_text_chunk(text, role, t0, t1, asr_ms=80.0)


def snapshot(call_id: str) -> dict:
    pipe = _live.get(call_id)
    if not pipe:
        return {"error": "no live pipeline for this call"}
    return pipe.summary()


def list_live() -> List[str]:
    return list(_live.keys())
