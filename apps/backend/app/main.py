"""FastAPI entrypoint.

Run: ``uvicorn app.main:app --reload --port 8000`` (from apps/backend).
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .errors import HackAIError
from .logging_conf import configure_logging, get_logger
from .routes import router

settings = get_settings()
configure_logging(settings.log_level)
log = get_logger("hackai.main")

app = FastAPI(
    title="HackAI — Artisan Listing Generator",
    version="0.1.0",
    description="Image + Darija voice -> premium English marketplace listing.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HackAIError)
async def hackai_error_handler(_: Request, exc: HackAIError) -> JSONResponse:
    """Domain errors -> clean JSON. Stack traces never leak to users."""
    log.warning("Handled error: %s (%s)", exc.message, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "detail": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    log.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Unexpected server error. Please try again."},
    )


app.include_router(router)


@app.get("/")
async def root() -> dict:
    return {"service": "hackai-backend", "docs": "/docs", "health": "/api/health"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )
