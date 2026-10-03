"""Sunfyre — grounded voice operations.

    uvicorn app:app --reload
    python -m app
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from q1_voice_agent.api import router as q1_router
from q2_knowledge_base.api import router as q2_router
from q3_native_bots.api import router as q3_router
from q4_live_nudges.api import router as q4_router

_ROOT = Path(__file__).resolve().parent

app = FastAPI(
    title="Sunfyre — grounded voice + KB + live nudges",
    version="1.0",
    description="Voice qualifier · Knowledge base · PH/ID bots · Live insights",
)
app.include_router(q2_router)
app.include_router(q1_router)
app.include_router(q3_router)
app.include_router(q4_router)
app.mount("/static", StaticFiles(directory=str(_ROOT / "static")), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(
        _ROOT / "static" / "home.html",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/docs/openapi", include_in_schema=False)
def spec_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/docs")


if __name__ == "__main__":
    import uvicorn
    from shared.config import settings
    uvicorn.run("app:app", host=settings.host, port=settings.port, reload=False)
