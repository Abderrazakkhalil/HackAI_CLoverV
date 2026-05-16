"""LLM product extraction via Groq (ported from the Hirafi pipeline).

Hard guarantees:
- Output is a schema-valid :class:`Product`, or an :class:`LLMError` is
  raised (no silent seeded substitution).
- Bad JSON -> sanitize + strict retry -> fallback model.
- Raw model text is never returned to callers.
"""

from __future__ import annotations

import json

from pydantic import ValidationError as PydanticValidationError

from ..config import get_settings
from ..errors import LLMError
from ..logging_conf import get_logger
from ..prompts import STRICT_RETRY_SUFFIX, SYSTEM_PROMPT, build_user_prompt
from ..schemas import Product

log = get_logger("hackai.llm")


def _strip_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    return raw.strip()


def _to_product(parsed: dict, transcript: str) -> Product:
    """Validate the LLM payload against the Product schema."""
    data = parsed.get("product", parsed)
    product = Product.model_validate(data)
    # The transcript is authoritative — never trust the model's echo.
    product.raw_transcript = transcript
    return product


def _call_groq(model: str, user_msg: str) -> str:
    from groq import Groq

    settings = get_settings()
    client = Groq(api_key=settings.groq_api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )
    return completion.choices[0].message.content or ""


def _extract_with_model(model: str, transcript: str) -> Product:
    """One model, with a strict retry on malformed/invalid output."""
    settings = get_settings()
    for attempt in range(settings.llm_max_retries + 1):
        user_msg = build_user_prompt(transcript)
        if attempt > 0:
            user_msg += STRICT_RETRY_SUFFIX
        raw = _strip_fences(_call_groq(model, user_msg))
        try:
            return _to_product(json.loads(raw), transcript)
        except (json.JSONDecodeError, PydanticValidationError) as exc:
            log.warning(
                "%s bad output (attempt %d): %s", model, attempt + 1, exc
            )
    raise ValueError(f"{model}: invalid output after retries")


def generate_product(transcription: str) -> tuple[Product, str]:
    """Return ``(Product, llm_model_label)``.

    Order: Groq primary -> Groq fallback model. No seeded last-resort:
    if extraction genuinely fails, that error is raised so it is
    visible, not hidden behind a fake listing.
    """
    settings = get_settings()

    if not settings.groq_api_key:
        raise LLMError(
            "Listing generation is not configured.",
            detail="GROQ_API_KEY is missing — set it in .env.",
        )

    last_exc: Exception | None = None
    for model in (settings.groq_primary_model, settings.groq_fallback_model):
        try:
            product = _extract_with_model(model, transcription)
            log.info("Extraction succeeded via %s", model)
            return product, f"{model}@groq"
        except Exception as exc:  # noqa: BLE001 - try next model
            last_exc = exc
            log.error("Model %s failed: %s", model, exc)

    raise LLMError(
        "The AI could not generate a listing. Please try again.",
        detail=f"{type(last_exc).__name__}: {last_exc}",
    )
