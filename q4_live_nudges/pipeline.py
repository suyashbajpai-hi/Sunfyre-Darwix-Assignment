"""Real-time insight pipeline.

A completed recording analysed only after upload does **not** qualify.
This module either:

* chunks a WAV and releases each chunk only after waiting `chunk_seconds`
  of wall-clock time (replay at real-time speed), or
* accepts live WebSocket / HTTP chunks as they arrive from the dashboard.

Each chunk: ASR → append transcript → rule (+ optional LLM) signals →
nudge controller → event for the UI. Component latencies are recorded.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from shared.asr import ASRResult, transcribe_bytes
from shared.audio import WavChunk, chunk_wav
from shared.config import RECORDINGS_DIR, settings
from shared.latency import LatencyStats

from .controls import Nudge, NudgeController
from .signals import DISCLOSURE_MARKERS, Signal, extract_rule_signals, maybe_llm_signals


@dataclass
class TranscriptLine:
    t_start: float
    t_end: float
    speaker: str
    text: str
    asr_latency_ms: float


@dataclass
class PipelineEvent:
    t: float
    kind: str  # transcript | nudge | suppressed | metric
    payload: dict


class LiveInsightPipeline:
    def __init__(self, call_id: str, asr_language: Optional[str] = None, vocabulary_prompt: Optional[str] = None):
        self.call_id = call_id
        self.asr_language = asr_language
        self.vocabulary_prompt = vocabulary_prompt
        self.transcript: List[TranscriptLine] = []
        self.controller = NudgeController()
        self.latency = LatencyStats()
        self.events: List[PipelineEvent] = []
        self.agent_disclosed = False
        self.listeners: List[Callable[[PipelineEvent], None]] = []

    def on_event(self, fn: Callable[[PipelineEvent], None]) -> None:
        self.listeners.append(fn)

    def _emit(self, kind: str, payload: dict, t: float) -> None:
        ev = PipelineEvent(t=t, kind=kind, payload=payload)
        self.events.append(ev)
        for fn in self.listeners:
            fn(ev)

    def ingest_text_chunk(self, text: str, speaker: str, t_start: float, t_end: float, asr_ms: float = 0.0) -> List[Nudge]:
        """Used by the simulator when we already have (or fake) a transcript chunk."""
        line = TranscriptLine(t_start, t_end, speaker, text, asr_ms)
        self.transcript.append(line)
        self.latency.add("asr", asr_ms)
        if speaker == "agent" and any(rx.search(text) for rx in DISCLOSURE_MARKERS):
            self.agent_disclosed = True
        self._emit("transcript", asdict(line), t_end)
        return self._signals_for(line)

    def ingest_audio_chunk(self, wav_bytes: bytes, speaker: str, t_start: float, t_end: float) -> List[Nudge]:
        t0 = time.perf_counter()
        asr: ASRResult = transcribe_bytes(
            wav_bytes, filename="chunk.wav",
            language=self.asr_language, vocabulary_prompt=self.vocabulary_prompt, verbose=False,
        )
        asr_ms = asr.latency_ms or (time.perf_counter() - t0) * 1000
        text = asr.text or ""
        if asr.fallback:
            text = text or ""
        return self.ingest_text_chunk(text, speaker, t_start, t_end, asr_ms=asr_ms)

    def check_missing_disclosure(self, t_end: float) -> List[Nudge]:
        if self.agent_disclosed or t_end < 8:
            return []
        sig = Signal(
            "compliance_gap", 0.9,
            "No recording/solicitation disclosure heard in the first seconds of the call.",
            t_end, "agent",
            {"nudge": "Required disclosure is missing. State name, company, recording consent before continuing."},
        )
        return self._accept(sig)

    def _signals_for(self, line: TranscriptLine) -> List[Nudge]:
        nudges: List[Nudge] = []
        t0 = time.perf_counter()
        rule = extract_rule_signals(line.text, line.speaker, line.t_end, self.agent_disclosed)
        window = "\n".join(f"{x.speaker}: {x.text}" for x in self.transcript[-8:])
        llm = maybe_llm_signals(window, line.t_end) if settings.q4_use_llm_signals else []
        self.latency.add("signal_extraction", (time.perf_counter() - t0) * 1000)
        seen = set()
        for sig in rule + llm:
            key = (sig.kind, sig.evidence[:80])
            if key in seen:
                continue
            seen.add(key)
            nudges.extend(self._accept(sig))
        if line.speaker == "agent":
            nudges.extend(self.check_missing_disclosure(line.t_end))
        return nudges

    def _accept(self, sig: Signal) -> List[Nudge]:
        t0 = time.perf_counter()
        n = self.controller.consider(sig)
        self.latency.add("nudge_control", (time.perf_counter() - t0) * 1000)
        if n is None:
            last = self.controller.suppressed[-1] if self.controller.suppressed else None
            if last:
                self._emit("suppressed", asdict(last), sig.t_end)
            return []
        t_deliv = time.perf_counter()
        self._emit("nudge", asdict(n), sig.t_end)
        self.latency.add("delivery", (time.perf_counter() - t_deliv) * 1000)
        # e2e from chunk time: asr + signal + control + delivery already sampled
        return [n]

    def summary(self) -> dict:
        e2e = []
        # approximate e2e as sum of component means is wrong; use asr+signal+control+delivery per event
        asr = self.latency.samples.get("asr") or [0]
        sig = self.latency.samples.get("signal_extraction") or [0]
        ctl = self.latency.samples.get("nudge_control") or [0]
        n = min(len(asr), len(sig), len(ctl)) or 1
        for i in range(n):
            e2e.append(asr[min(i, len(asr) - 1)] + sig[min(i, len(sig) - 1)] + ctl[min(i, len(ctl) - 1)])
        for v in e2e:
            self.latency.add("e2e_chunk", v)
        return {
            "call_id": self.call_id,
            "transcript": [asdict(x) for x in self.transcript],
            "nudges": [asdict(n) for n in self.controller.emitted],
            "suppressed": [asdict(n) for n in self.controller.suppressed],
            "controller": self.controller.stats(),
            "latency": self.latency.summary(),
            "agent_disclosed": self.agent_disclosed,
        }

    def save(self) -> Path:
        path = RECORDINGS_DIR / "live_sessions" / f"{self.call_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.summary(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path


def replay_wav_realtime(path: Path, pipeline: LiveInsightPipeline, speaker: str = "mixed",
                        realtime: bool = True) -> dict:
    chunks = chunk_wav(path, settings.q4_chunk_seconds)
    for ch in chunks:
        wall0 = time.perf_counter()
        pipeline.ingest_audio_chunk(ch.wav_bytes, speaker, ch.start_s, ch.end_s)
        if realtime:
            spent = time.perf_counter() - wall0
            wait = max(0.0, settings.q4_chunk_seconds - spent)
            if wait:
                time.sleep(wait)
    return pipeline.summary()
