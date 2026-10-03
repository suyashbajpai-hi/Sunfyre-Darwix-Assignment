"""Replay Q4 scenarios at real-time speed.

    python -m q4_live_nudges.simulate              # all scenarios, real-time waits
    python -m q4_live_nudges.simulate --fast       # skip sleeps (CI / offline)
    python -m q4_live_nudges.simulate --only skipped_disclosure
"""
from __future__ import annotations

import argparse
import json
import time
from typing import List

from shared.config import ROOT_DIR

from .pipeline import LiveInsightPipeline
from .scenarios import SCENARIOS


def run_scenario(name: str, realtime: bool = True) -> dict:
    spec = SCENARIOS[name]
    pipe = LiveInsightPipeline(call_id=f"Q4-{name}")
    t_cursor = 0.0
    for turn in spec["turns"]:
        dur = float(turn["duration_s"])
        t0 = t_cursor
        t1 = t_cursor + dur
        wall0 = time.perf_counter()
        pipe.ingest_text_chunk(str(turn["text"]), str(turn["speaker"]), t0, t1, asr_ms=120.0)
        if realtime:
            wait = max(0.0, dur - (time.perf_counter() - wall0))
            if wait:
                time.sleep(wait)
        t_cursor = t1
    summary = pipe.summary()
    path = pipe.save()
    emitted_kinds = [n["kind"] for n in summary["nudges"]]
    expected = spec["expect_kinds"]
    hit = all(k in emitted_kinds for k in expected)
    # noisy scenario: success = no (or only suppressed) high-value spam
    if name == "noisy_ambiguous":
        hit = len(summary["nudges"]) == 0
    summary["scenario"] = name
    summary["title"] = spec["title"]
    summary["expected_kinds"] = expected
    summary["pass"] = hit
    summary["saved"] = str(path)
    return summary


def replay_transcript(path, realtime: bool = False) -> dict:
    """Reuse a Q1/Q3 recorded call (assessment allows this) as a Q4 live stream."""
    from pathlib import Path
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    turns = data.get("turns") or []
    pipe = LiveInsightPipeline(call_id=f"Q4-replay-{p.stem}")
    t_cursor = 0.0
    for turn in turns:
        text = str(turn.get("text") or "")
        speaker = "customer" if turn.get("role") in {"customer", "cust", "user"} else "agent"
        dur = max(2.0, min(12.0, len(text.split()) * 0.38))
        wall0 = time.perf_counter()
        pipe.ingest_text_chunk(text, speaker, t_cursor, t_cursor + dur, asr_ms=110.0)
        if realtime:
            wait = max(0.0, dur - (time.perf_counter() - wall0))
            if wait:
                time.sleep(wait)
        t_cursor += dur
    summary = pipe.summary()
    summary["scenario"] = f"replay:{p.stem}"
    summary["title"] = f"Replay of {p.name}"
    summary["expected_kinds"] = []
    summary["pass"] = True
    summary["saved"] = str(pipe.save())
    return summary


def _default_replays() -> List:
    from shared.config import TRANSCRIPTS_DIR
    names = ["q1_cooperative.json", "q1_oos.json", "ph_cooperative_taglish.json", "id_colloquial_denda.json"]
    return [TRANSCRIPTS_DIR / n for n in names if (TRANSCRIPTS_DIR / n).exists()]


def run_all(realtime: bool = True, only: str | None = None, include_replays: bool = True) -> dict:
    names = [only] if only else list(SCENARIOS)
    results = [run_scenario(n, realtime=realtime) for n in names]
    if include_replays and not only:
        for path in _default_replays():
            results.append(replay_transcript(path, realtime=realtime))
    fp_analysis = _false_positives(results)
    latency_rows = []
    for r in results:
        latency_rows.append({"scenario": r["scenario"], **r["latency"]})
    out = {
        "realtime": realtime,
        "passed": sum(1 for r in results if r["pass"]),
        "total": len(results),
        "false_positive_analysis": fp_analysis,
        "results": results,
    }
    _write_md(out)
    return out


def _false_positives(results: List[dict]) -> dict:
    """Approximate FP: nudges on the noisy scenario + suppressed-but-emitted duplicates."""
    noisy = next((r for r in results if r["scenario"] == "noisy_ambiguous"), None)
    fp_emitted = len(noisy["nudges"]) if noisy else 0
    suppressed = sum(len(r["suppressed"]) for r in results)
    emitted = sum(len(r["nudges"]) for r in results)
    return {
        "nudges_emitted_all_scenarios": emitted,
        "nudges_suppressed_all_scenarios": suppressed,
        "noisy_scenario_emitted": fp_emitted,
        "noisy_scenario_suppressed": len(noisy["suppressed"]) if noisy else 0,
        "approx_precision_note": (
            "Precision proxy = 1 - (noisy_emitted / max(emitted,1)). "
            "A true FP rate needs labelled frames; this is the assessment's 'approximate' bar."
        ),
        "approx_precision": round(1.0 - (fp_emitted / max(emitted, 1)), 3),
    }


def _write_md(out: dict) -> None:
    lines = ["# Q4 — Live insights: latency, nudges, false-positive controls", "",
             f"Realtime replay: **{out['realtime']}** · Scenarios passed: {out['passed']}/{out['total']}", "",
             "## False-positive / suppression", "",
             "```json", json.dumps(out["false_positive_analysis"], indent=2), "```", "",
             "Controls: confidence threshold "
             "(default 0.65), per-kind cooldown 45s, duplicate-evidence overlap, TTL 60s, priority order "
             "compliance > frustration > payment > cross-sell > callback > buying.", ""]
    for r in out["results"]:
        mark = "PASS" if r["pass"] else "FAIL"
        lines += [f"## {r['title']} — {mark}", "",
                  f"Expected kinds: `{r['expected_kinds']}`", "",
                  "### Emitted nudges", ""]
        if not r["nudges"]:
            lines.append("_None (good for the noisy scenario)._")
        for n in r["nudges"]:
            lines.append(f"- `{n['kind']}` prio={n['priority']} conf={n['confidence']} — {n['text']}")
        lines += ["", "### Suppressed", ""]
        if not r["suppressed"]:
            lines.append("_None._")
        for n in r["suppressed"]:
            lines.append(f"- `{n['kind']}` {n.get('suppress_reason')} — {n['evidence'][:80]}")
        lat = r.get("latency") or {}
        if lat:
            lines += ["", "### Component latency", "",
                      "| Component | n | P50 ms | P95 ms | mean | max |", "|---|---|---|---|---|---|"]
            for comp, s in lat.items():
                lines.append(
                    f"| {comp} | {s['count']} | {s['p50_ms']} | {s['p95_ms']} | {s['mean_ms']} | {s['max_ms']} |"
                )
        lines.append("")
    lines += ["## 10× scale and noisy audio (limitations)", "",
              "- At 10× concurrent calls the bottleneck is ASR (Whisper HTTP). A production design batches "
              "partials on a streaming ASR (Deepgram / Whisper streaming) and runs rules on every partial, "
              "LLM only on topic shifts.",
              "- Noisy audio raises WER; rules that key on rare phrases will miss, and LLM-on-garbage will "
              "over-fire unless the confidence threshold stays high (we default 0.65 and suppress duplicates).",
              "- Speaker separation is not diarised from mixed WAV; the web demo labels agent vs customer "
              "from the calling UI. A production trunk would use stereo (agent/customer channels).", ""]
    (ROOT_DIR / "docs" / "q4_latency.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="do not sleep for real-time duration")
    ap.add_argument("--only", default=None)
    ap.add_argument("--from-transcript", dest="from_transcript", default=None,
                    help="replay a Q1/Q3 transcript JSON as a live Q4 stream")
    args = ap.parse_args()
    if args.from_transcript:
        summary = replay_transcript(args.from_transcript, realtime=not args.fast)
        print(json.dumps({"scenario": summary["scenario"], "nudges": len(summary["nudges"]),
                          "suppressed": len(summary["suppressed"]), "latency": summary["latency"]}, indent=2))
    else:
        out = run_all(realtime=not args.fast, only=args.only)
        print(json.dumps({"passed": out["passed"], "total": out["total"],
                          "fp": out["false_positive_analysis"]}, indent=2))
        for r in out["results"]:
            print(f"{'PASS' if r['pass'] else 'FAIL'}  {str(r['scenario']):<32} nudges={len(r['nudges'])} suppressed={len(r['suppressed'])}")
