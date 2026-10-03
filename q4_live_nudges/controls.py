"""Nudge control plane: threshold, duplicate suppression, cooldown, priority, TTL.

Without this, a live coach dumps low-value alerts (a rejection condition).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from shared.config import settings

from .signals import Signal

PRIORITY = {
    "compliance_gap": 100,
    "rising_frustration": 90,
    "payment_difficulty": 70,
    "missed_cross_sell": 60,
    "callback_need": 50,
    "buying_signal": 40,
    "topic_shift": 20,
}


@dataclass
class Nudge:
    id: str
    kind: str
    text: str
    confidence: float
    priority: int
    created_t: float
    expires_t: float
    evidence: str
    suppressed: bool = False
    suppress_reason: Optional[str] = None


@dataclass
class NudgeController:
    emitted: List[Nudge] = field(default_factory=list)
    suppressed: List[Nudge] = field(default_factory=list)
    last_by_kind: Dict[str, float] = field(default_factory=dict)
    _n = 0

    def consider(self, sig: Signal) -> Optional[Nudge]:
        self._n += 1
        nid = f"N{self._n:03d}"
        pri = PRIORITY.get(sig.kind, 10)
        nudge = Nudge(
            id=nid, kind=sig.kind,
            text=sig.details.get("nudge") or f"Signal: {sig.kind}",
            confidence=sig.confidence, priority=pri,
            created_t=sig.t_end, expires_t=sig.t_end + settings.q4_nudge_ttl_seconds,
            evidence=sig.evidence,
        )
        if sig.confidence < settings.q4_confidence_threshold:
            nudge.suppressed = True
            nudge.suppress_reason = f"below_threshold {sig.confidence:.2f}<{settings.q4_confidence_threshold}"
            self.suppressed.append(nudge)
            return None
        last = self.last_by_kind.get(sig.kind)
        if last is not None and (sig.t_end - last) < settings.q4_cooldown_seconds:
            nudge.suppressed = True
            nudge.suppress_reason = f"cooldown {sig.kind} last={last:.1f}s"
            self.suppressed.append(nudge)
            return None
        # near-duplicate evidence
        for prev in self.emitted[-6:]:
            if prev.kind == sig.kind and _overlap(prev.evidence, sig.evidence) > 0.6:
                nudge.suppressed = True
                nudge.suppress_reason = "duplicate_evidence"
                self.suppressed.append(nudge)
                return None
        self.last_by_kind[sig.kind] = sig.t_end
        self.emitted.append(nudge)
        return nudge

    def active(self, now_t: float) -> List[Nudge]:
        return [n for n in self.emitted if n.expires_t >= now_t]

    def stats(self) -> dict:
        return {
            "emitted": len(self.emitted),
            "suppressed": len(self.suppressed),
            "by_kind_emitted": _count(self.emitted),
            "by_kind_suppressed": _count(self.suppressed),
            "suppress_reasons": _count(self.suppressed, key="suppress_reason"),
        }


def _overlap(a: str, b: str) -> float:
    sa, sb = set(a.lower().split()), set(b.lower().split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _count(items, key: str = "kind") -> dict:
    d: Dict[str, int] = {}
    for it in items:
        k = getattr(it, key) or "unknown"
        d[k] = d.get(k, 0) + 1
    return d
