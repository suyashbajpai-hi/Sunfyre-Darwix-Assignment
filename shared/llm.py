"""Thin LLM wrapper around the OpenAI chat API.

Features:
- JSON-mode helper that always returns a dict (never raises on malformed JSON)
- call latency recorded in milliseconds
- deterministic, clearly-labelled fallback when no API key is configured so the
  rest of the system (KB, dashboards, test harnesses) still runs end-to-end.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .config import settings

log = logging.getLogger(__name__)

_client = None


def get_client():
    """Lazily construct the client. Supports OpenAI or Google Gemini (via OpenAI-compatible endpoint)."""
    global _client
    if _client is not None:
        return _client
    if not settings.has_llm:
        return None
    from openai import OpenAI

    if settings.has_gemini and not settings.has_openai:
        base_url = settings.openai_base_url or "https://generativelanguage.googleapis.com/v1beta/openai/"
        _client = OpenAI(api_key=settings.gemini_api_key, base_url=base_url)
    else:
        kwargs: Dict[str, Any] = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        _client = OpenAI(**kwargs)
    return _client


@dataclass
class LLMResult:
    text: str
    latency_ms: float
    model: str
    usage: Dict[str, int]
    fallback: bool = False


def chat(
    messages: List[Dict[str, str]],
    *,
    temperature: float = 0.2,
    max_tokens: int = 400,
    json_mode: bool = False,
    model: Optional[str] = None,
) -> LLMResult:
    client = get_client()
    model = model or settings.active_llm_model
    t0 = time.perf_counter()
    if client is None:
        log.warning("No LLM key configured (OPENAI_API_KEY or GEMINI_API_KEY) - returning fallback response")
        text = "{}" if json_mode else "[LLM unavailable: API key not configured]"
        return LLMResult(text=text, latency_ms=0.0, model="none", usage={}, fallback=True)

    kwargs: Dict[str, Any] = dict(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    try:
        resp = client.chat.completions.create(**kwargs)
        latency = (time.perf_counter() - t0) * 1000.0
        text = resp.choices[0].message.content or ""
        usage = {}
        if resp.usage:
            usage = {"prompt_tokens": resp.usage.prompt_tokens, "completion_tokens": resp.usage.completion_tokens}
        return LLMResult(text=text, latency_ms=latency, model=model, usage=usage)
    except Exception as exc:
        log.error("OpenAI chat failed: %s", exc)
        text = "{}" if json_mode else f"[LLM unavailable: {exc}]"
        return LLMResult(text=text, latency_ms=(time.perf_counter() - t0) * 1000.0, model=model, usage={}, fallback=True)


def chat_json(messages: List[Dict[str, str]], **kw) -> Dict[str, Any]:
    """Call the LLM in JSON mode and parse; returns {} on any parse failure."""
    import re
    result = chat(messages, json_mode=True, **kw)
    raw = result.text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw).strip()
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            data["_latency_ms"] = result.latency_ms
            data["_fallback"] = result.fallback
            return data
    except json.JSONDecodeError:
        log.warning("LLM returned non-JSON in json_mode: %s", result.text[:200])
    return {"_latency_ms": result.latency_ms, "_fallback": result.fallback}
