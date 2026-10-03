"""Q4 dashboard + HTTP/WebSocket nudge stream."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from .scenarios import SCENARIOS
from .simulate import replay_transcript, run_scenario
from .bridge import list_live, snapshot

router = APIRouter(prefix="/live", tags=["Q4 Live insights"])
_UI = Path(__file__).parent / "static" / "dashboard.html"
_sockets: Set[WebSocket] = set()
_last: dict = {}


@router.get("", response_class=HTMLResponse, include_in_schema=False)
def ui():
    return HTMLResponse(_UI.read_text(encoding="utf-8"),
                        headers={"Cache-Control": "no-store, no-cache, must-revalidate"})


@router.get("/scenarios")
def scenarios():
    return {k: {"title": v["title"], "expect_kinds": v["expect_kinds"], "turns": len(v["turns"])}
            for k, v in SCENARIOS.items()}


@router.post("/run/{name}")
async def run(name: str, fast: bool = True):
    if name not in SCENARIOS and name != "all":
        return {"error": "unknown scenario"}
    names = list(SCENARIOS) if name == "all" else [name]
    results = []
    for n in names:
        summary = run_scenario(n, realtime=not fast)
        _last[n] = summary
        await _broadcast({"type": "scenario_done", "name": n, "summary": summary})
        results.append({"name": n, "pass": summary["pass"], "nudges": summary["nudges"],
                        "suppressed": len(summary["suppressed"]), "latency": summary["latency"]})
    return {"results": results}


@router.get("/last/{name}")
def last(name: str):
    return _last.get(name) or {"error": "run the scenario first"}


@router.get("/session/{call_id}")
def live_session(call_id: str):
    return snapshot(call_id)


@router.get("/attached")
def attached():
    return {"call_ids": list_live()}


@router.post("/replay-transcript/{stem}")
async def replay(stem: str, fast: bool = True):
    from shared.config import TRANSCRIPTS_DIR
    path = TRANSCRIPTS_DIR / f"{stem}.json"
    if not path.exists():
        return {"error": f"missing {path.name} — run the Q1/Q3 test_calls first"}
    summary = replay_transcript(path, realtime=not fast)
    _last[f"replay:{stem}"] = summary
    await _broadcast({"type": "scenario_done", "name": f"replay:{stem}", "summary": summary})
    return {"name": f"replay:{stem}", "nudges": summary["nudges"], "suppressed": len(summary["suppressed"]),
            "latency": summary["latency"]}


@router.websocket("/ws")
async def ws(sock: WebSocket):
    await sock.accept()
    _sockets.add(sock)
    try:
        while True:
            await sock.receive_text()
    except WebSocketDisconnect:
        _sockets.discard(sock)


async def _broadcast(msg: dict) -> None:
    dead = []
    data = json.dumps(msg, default=str)
    for s in _sockets:
        try:
            await s.send_text(data)
        except Exception:  # noqa: BLE001
            dead.append(s)
    for s in dead:
        _sockets.discard(s)
