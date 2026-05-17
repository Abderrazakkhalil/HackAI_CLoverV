"""Multilingual social content generation via Groq.

Mirrors the product-extraction philosophy in ``services/llm.py``:
strict JSON, schema-validate, retry on bad output, fall back to the
secondary model, and raise a typed error rather than return junk.
"""

from __future__ import annotations

import json

from pydantic import ValidationError as PydanticValidationError

from ...config import get_settings
from ...logging_conf import get_logger
from ..llm import _strip_fences  # reuse the existing JSON sanitizer
from .social_exceptions import SocialConfigError, SocialGenerationError
from .social_models import SocialContentBundle, SocialGenerationInput

log = get_logger("hackai.social.gen")

SYSTEM_PROMPT = """\
You are an expert social-media marketer for premium Moroccan artisan \
products sold internationally. You craft scroll-stopping, culturally \
authentic copy that converts.

You ALWAYS return a SINGLE valid JSON object and nothing else — no \
markdown, no commentary.

Produce Facebook content in three languages (en, fr, ar). For EACH \
language provide:
- caption
- cta  (a short call-to-action line)
- hashtags (array)

Facebook style: longer, descriptive, storytelling about the craft, \
origin and the artisan; warm and authentic; fewer emojis.

Hashtag rules:
- at most 10 per language
- a balanced mix of: niche, artisan, Moroccan, and product-category tags
- no spaces inside a tag; '#' optional (it will be normalized)

Arabic must be fluent Modern Standard Arabic. French must be native \
quality. English must be native, market-appropriate for the target \
market.
"""


def _build_user_prompt(data: SocialGenerationInput) -> str:
    return (
        "Create the social content for this product.\n\n"
        f"product_title: {data.product_title}\n"
        f"marketing_description: {data.marketing_description}\n"
        f"price_mad: {data.price_mad}\n"
        f"price_usd: {data.price_usd}\n"
        f"origin: {data.origin}\n"
        f"materials: {', '.join(data.materials)}\n"
        f"target_market: {data.target_market}\n\n"
        "Return JSON with EXACTLY this shape:\n"
        '{\n'
        '  "facebook": {\n'
        '    "en": {"caption": "", "cta": "", "hashtags": []},\n'
        '    "fr": {"caption": "", "cta": "", "hashtags": []},\n'
        '    "ar": {"caption": "", "cta": "", "hashtags": []}\n'
        '  }\n'
        '}\n'
        "Return ONLY this JSON object."
    )


_RETRY_SUFFIX = (
    "\n\nYour previous reply was not valid. Return ONLY the JSON object "
    "with the exact keys requested. No prose, no code fences."
)


def _call_groq(model: str, system: str, user: str) -> str:
    from groq import Groq

    settings = get_settings()
    client = Groq(api_key=settings.groq_api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.8,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )
    return completion.choices[0].message.content or ""


def _generate_with_model(
    model: str, data: SocialGenerationInput
) -> SocialContentBundle:
    settings = get_settings()
    base_user = _build_user_prompt(data)
    for attempt in range(settings.llm_max_retries + 1):
        user = base_user if attempt == 0 else base_user + _RETRY_SUFFIX
        raw = _strip_fences(_call_groq(model, SYSTEM_PROMPT, user))
        try:
            return SocialContentBundle.model_validate(json.loads(raw))
        except (json.JSONDecodeError, PydanticValidationError) as exc:
            log.warning(
                "%s social output invalid (attempt %d): %s",
                model, attempt + 1, exc,
            )
    raise ValueError(f"{model}: invalid social content after retries")


def generate_social_content(
    data: SocialGenerationInput,
) -> SocialContentBundle:
    """Return a validated :class:`SocialContentBundle`.

    Groq primary → fallback model. Raises :class:`SocialGenerationError`
    if both fail (never returns unvalidated content).
    """
    settings = get_settings()
    if not settings.groq_api_key:
        raise SocialConfigError(
            "Social generation is not configured.",
            details="GROQ_API_KEY is missing — set it in .env.",
        )

    last_exc: Exception | None = None
    for model in (settings.groq_primary_model, settings.groq_fallback_model):
        try:
            bundle = _generate_with_model(model, data)
            log.info("Social content generated via %s", model)
            return bundle
        except Exception as exc:  # noqa: BLE001 - try fallback model
            last_exc = exc
            log.error("Social model %s failed: %s", model, exc)

    raise SocialGenerationError(
        details=f"{type(last_exc).__name__}: {last_exc}"
    )
