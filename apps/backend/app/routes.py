"""HTTP API consumed by the Hirfati frontend."""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from .config import get_settings
from .demo_data import DEMO_PRODUCTS
from .errors import ValidationError
from .logging_conf import get_logger
from .schemas import GenerateRequest, ProcessResponse, Product
from .services.llm import generate_product
from .services.orchestrator import run_pipeline

log = get_logger("hackai.api")
router = APIRouter(prefix="/api")


@router.get("/health")
async def health() -> dict:
    s = get_settings()
    return {
        "status": "ok",
        "demo_mode": s.demo_mode,
        "pipeline_version": s.pipeline_version,
        "providers": {
            "moulsot": bool(s.hf_token),
            "groq": bool(s.groq_api_key),
        },
    }


@router.post("/process", response_model=ProcessResponse)
async def process(
    audio: UploadFile = File(...),
    image: UploadFile | None = File(default=None),
) -> ProcessResponse:
    """Full pipeline: audio (+ optional image) -> rich product listing."""
    audio_bytes = await audio.read()
    image_bytes = await image.read() if image is not None else None
    return await run_pipeline(
        audio_bytes=audio_bytes,
        audio_filename=audio.filename or "audio.webm",
        audio_content_type=audio.content_type,
        image_bytes=image_bytes or None,
        image_filename=image.filename if image else None,
        image_content_type=image.content_type if image else None,
    )


@router.post("/generate", response_model=Product)
async def generate(req: GenerateRequest) -> Product:
    """Text-only path (useful for testing without recording audio)."""
    if not req.transcription.strip():
        raise ValidationError("Transcription text is required.")
    product, label = generate_product(req.transcription)
    log.info("Listing extracted via %s (text endpoint)", label)
    return product


@router.get("/demo-products", response_model=dict[str, Product])
async def demo_products() -> dict[str, Product]:
    """Seeded products — backs the demo gallery and MCP resources."""
    return DEMO_PRODUCTS
