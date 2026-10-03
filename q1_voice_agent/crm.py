"""Mock CRM + optional escalation webhook (Question 1 optional business action)."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

import httpx

from shared.config import settings

log = logging.getLogger(__name__)


def _crm_path() -> Path:
    p = settings.crm_file
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def create_lead(payload: Dict[str, Any]) -> Dict[str, Any]:
    rec = {
        "lead_id": "LD-" + uuid4().hex[:8].upper(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        **payload,
    }
    path = _crm_path()
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    log.info("CRM lead written %s -> %s", rec["lead_id"], path)
    return rec


def list_leads(limit: int = 50) -> list:
    path = _crm_path()
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(out))


def post_escalation(payload: Dict[str, Any]) -> Optional[str]:
    url = settings.escalation_webhook_url
    if not url:
        log.info("No ESCALATION_WEBHOOK_URL set; escalation stored on the lead only")
        return None
    try:
        r = httpx.post(url, json=payload, timeout=8.0)
        return f"{r.status_code}"
    except Exception as exc:  # noqa: BLE001
        log.warning("escalation webhook failed: %s", exc)
        return f"error: {exc}"
