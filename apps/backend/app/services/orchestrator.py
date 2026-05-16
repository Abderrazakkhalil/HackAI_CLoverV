"""Pipeline orchestration: audio (+image) -> transcription -> product+meta.

This is the one function both the REST API and the MCP server call so the
behaviour is identical no matter how Hirafi is driven. Blocking SDK calls
(gradio_client, groq) run in worker threads so FastAPI stays async.
"""

from __future__ import annotations

import asyncio
import base64
from datetime import datetime, timezone

from ..config import get_settings
from ..errors import ValidationError
from ..logging_conf import get_logger
from ..schemas import Meta, ProcessResponse
from .llm import generate_product
from .transcription import transcribe

log = get_logger("hackai.pipeline")


def _image_to_data_url(image_bytes: bytes, content_type: str) -> str:
    b64 = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{content_type};base64,{b64}"


def validate_image(filename: str, content_type: str | None, size: int) -> None:
    settings = get_settings()
    if size <= 0:
        raise ValidationError("The image file is empty.")
    if size > settings.max_image_bytes:
        raise ValidationError(
            f"Image is too large (max {settings.max_image_bytes // (1024 * 1024)} MB)."
        )
    ct = (content_type or "").lower().split(";")[0].strip()
    ext_ok = filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    if ct and ct not in settings.allowed_image_types and not ext_ok:
        raise ValidationError(f"Unsupported image format: {ct or filename}")


async def run_pipeline(
    audio_bytes: bytes,
    audio_filename: str,
    audio_content_type: str | None,
    image_bytes: bytes | None = None,
    image_filename: str | None = None,
    image_content_type: str | None = None,
) -> ProcessResponse:
    settings = get_settings()

    image_data_url: str | None = None
    if image_bytes:
        validate_image(image_filename or "image", image_content_type, len(image_bytes))
        image_data_url = _image_to_data_url(
            image_bytes, image_content_type or "image/jpeg"
        )

    transcription, inference_ms = await asyncio.to_thread(
        transcribe, audio_bytes, audio_filename, audio_content_type
    )
    log.info("Transcription source=%s", transcription.source)

    product, llm_label = await asyncio.to_thread(
        generate_product, transcription.text
    )
    log.info("Listing extracted via %s", llm_label)

    meta = Meta(
        pipeline_version=settings.pipeline_version,
        asr_model="moulsot-v0.3",
        asr_provider=f"Gradio Space ({settings.asr_space})",
        llm_model=llm_label,
        processed_at=datetime.now(timezone.utc).isoformat(),
        audio_filename=audio_filename,
        inference_ms=inference_ms,
    )

    return ProcessResponse(
        product=product,
        meta=meta,
        transcription=transcription,
        image_data_url=image_data_url,
        demo_mode=settings.demo_mode,
    )
