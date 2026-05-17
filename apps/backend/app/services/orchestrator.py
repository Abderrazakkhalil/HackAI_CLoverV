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
from ..schemas import Artisan, Meta, ProcessResponse, SpeechLang
from .llm import generate_product
from .price_recommendation import recommend as recommend_price
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
    artisan: Artisan | None = None,
    speech_lang: SpeechLang = "darija",
) -> ProcessResponse:
    settings = get_settings()

    image_data_url: str | None = None
    if image_bytes:
        validate_image(image_filename or "image", image_content_type, len(image_bytes))
        image_data_url = _image_to_data_url(
            image_bytes, image_content_type or "image/jpeg"
        )

    log.info("Starting transcription: speech_lang=%s, audio_bytes=%d, filename=%s", speech_lang, len(audio_bytes), audio_filename)
    transcription, inference_ms = await asyncio.to_thread(
        transcribe, audio_bytes, audio_filename, audio_content_type, speech_lang
    )
    log.info("Transcription complete: source=%s, text_len=%d, inference_ms=%d", transcription.source, len(transcription.text), inference_ms)

    log.info("Starting LLM generation from transcription...")
    product, llm_label = await asyncio.to_thread(
        generate_product, transcription.text
    )
    log.info("LLM generation complete: model=%s, title_en=%s", llm_label, product.title.en[:50])

    # InDrive-style price flow: if the artisan didn't mention a price,
    # ask the recommender for an AI-suggested one.
    # We rely on price_mentioned (explicit LLM flag) rather than amount==0
    # because the LLM may hallucinate a plausible-looking amount even when
    # the transcript had no price. The flag is a much harder signal to fake.
    price_source = "extracted"
    price_recommendation = None
    log.info(
        "LLM price extraction: amount=%.2f, price_mentioned=%s",
        product.price.amount,
        product.price_mentioned,
    )
    if not product.price_mentioned:
        log.info("No price mentioned in transcript; triggering AI recommendation")
        try:
            rec, _comps = await asyncio.to_thread(recommend_price, product)
            if rec.suggested > 0:
                product.price.amount = rec.suggested
                product.price.currency = rec.currency
                product.price.price_usd_estimate = round(rec.suggested * 0.099, 2)
                price_source = "ai_recommended"
                price_recommendation = rec
            else:
                log.warning("Recommender returned suggested=0 — no comparables found; price left empty")
        except Exception as exc:  # noqa: BLE001 - never block listing on rec failure
            log.error("Price recommendation failed: %s", exc)

    if speech_lang == "amazigh":
        asr_model = "tamazight-nlp-asr"
        asr_provider = f"Gradio Space ({settings.amazigh_asr_space})"
    else:
        asr_model = "moulsot-v0.3"
        asr_provider = f"Gradio Space ({settings.asr_space})"

    meta = Meta(
        pipeline_version=settings.pipeline_version,
        asr_model=asr_model,
        asr_provider=asr_provider,
        llm_model=llm_label,
        processed_at=datetime.now(timezone.utc).isoformat(),
        audio_filename=audio_filename,
        inference_ms=inference_ms,
        price_source=price_source,
        price_recommendation=price_recommendation,
    )

    return ProcessResponse(
        product=product,
        meta=meta,
        transcription=transcription,
        artisan=artisan,
        image_data_url=image_data_url,
    )
