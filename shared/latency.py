"""Latency instrumentation: component timers and percentile reports."""
from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, Iterator, List


def percentile(values: List[float], p: float) -> float:
    """Nearest-rank percentile (p in 0..100). Returns 0.0 for empty input."""
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1)))))
    return s[k]


@dataclass
class LatencyStats:
    """Collects millisecond samples per named component."""

    samples: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))

    def add(self, component: str, ms: float) -> None:
        self.samples[component].append(float(ms))

    @contextmanager
    def timer(self, component: str) -> Iterator[None]:
        t0 = time.perf_counter()
        try:
            yield
        finally:
            self.add(component, (time.perf_counter() - t0) * 1000.0)

    def summary(self) -> Dict[str, Dict[str, float]]:
        out: Dict[str, Dict[str, float]] = {}
        for comp, vals in self.samples.items():
            if not vals:
                continue
            out[comp] = {
                "count": len(vals),
                "p50_ms": round(percentile(vals, 50), 1),
                "p95_ms": round(percentile(vals, 95), 1),
                "max_ms": round(max(vals), 1),
                "mean_ms": round(sum(vals) / len(vals), 1),
            }
        return out

    def to_markdown(self) -> str:
        rows = ["| Component | Count | P50 (ms) | P95 (ms) | Mean (ms) | Max (ms) |", "|---|---|---|---|---|---|"]
        for comp, s in self.summary().items():
            rows.append(f"| {comp} | {s['count']} | {s['p50_ms']} | {s['p95_ms']} | {s['mean_ms']} | {s['max_ms']} |")
        return "\n".join(rows)


def now_ms() -> float:
    return time.perf_counter() * 1000.0
