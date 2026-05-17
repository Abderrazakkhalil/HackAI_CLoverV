"""FastAPI entrypoint.

Run: ``uvicorn app.main:app --reload --port 8000`` (from apps/backend).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.social import router as social_router
from .config import get_settings
from .errors import HackAIError
from .logging_conf import configure_logging, get_logger
from .routes import router
from .services.social.scheduler_service import scheduler_service
from .services.social.social_exceptions import SocialError

settings = get_settings()
configure_logging(settings.log_level)
log = get_logger("hackai.main")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Scheduler runs in the API process; pending jobs are reloaded from
    # SQLite so scheduled posts survive restarts.
    scheduler_service.start()
    try:
        yield
    finally:
        scheduler_service.shutdown()


app = FastAPI(
    title="Hirfati — Artisan Listing & Social Commerce",
    version="0.2.0",
    description="Darija voice -> listing -> multilingual social posts.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(SocialError)
async def social_error_handler(_: Request, exc: SocialError) -> JSONResponse:
    """Social errors render the required nested envelope."""
    log.warning("Social error [%s]: %s (%s)",
                exc.code, exc.message, exc.details)
    return JSONResponse(status_code=exc.status_code, content=exc.to_envelope())


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
app.include_router(social_router)


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
