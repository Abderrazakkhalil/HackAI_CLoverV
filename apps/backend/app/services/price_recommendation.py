"""LLM-based price recommendation (InDrive-style).

Flow:
1. Query Supabase for published listings in the same category (and
   ideally sharing materials with the target).
2. Score & rerank candidates in Python by attribute overlap +
   dimensional similarity, keep the top-K.
3. Ask Groq to act as a Moroccan handicraft pricing expert: produce
   ``{suggested, min, max, currency, confidence, reasoning}`` JSON.
4. Validate / clamp. On any failure, fall back to the median of the
   comparables with low confidence.
"""

from __future__ import annotations

import json
import statistics
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from ..config import get_settings
from ..logging_conf import get_logger
from ..schemas import PriceRecommendation, Product

log = get_logger("hackai.recommend")


# ---------------------------------------------------------------------------
# Candidate retrieval + rerank
# ---------------------------------------------------------------------------
_SELECT_COLS = (
    "id,category,subcategory,tags,materials,colors,dimensions,"
    "price_amount,price_currency,origin,condition,title_en"
)


def _fresh_query(sb: Any) -> Any:
    """Return a new base query — must be called each time to avoid builder mutation."""
    return (
        sb.table("listings")
        .select(_SELECT_COLS)
        .eq("status", "published")
        .gt("price_amount", 0)
    )


def _fetch_candidates(product: Product) -> list[dict[str, Any]]:
    """Fetch up to 50 published comparables with a 3-level fallback.

    1. Same category + materials overlap (most specific)
    2. Same category only
    3. Any published listing (last resort — ensures we always have data)

    A fresh query is built for each level because the postgrest-py query
    builder mutates in-place, so reusing a base object carries over filters.
    """
    from supabase import create_client
    from ..config import get_settings

    settings = get_settings()
    sb = create_client(settings.supabase_url, settings.supabase_service_key)

    # --- level 1: category + materials overlap ---
    if product.category and product.materials:
        try:
            rows = (
                _fresh_query(sb)
                .eq("category", product.category)
                .overlaps("materials", product.materials)
                .limit(50)
                .execute()
                .data or []
            )
            if rows:
                log.info("candidates: %d rows (category+materials)", len(rows))
                return rows
        except Exception as exc:  # noqa: BLE001
            log.debug("materials overlap filter failed: %s", exc)

    # --- level 2: category only ---
    if product.category:
        rows = (
            _fresh_query(sb)
            .eq("category", product.category)
            .limit(50)
            .execute()
            .data or []
        )
        if rows:
            log.info("candidates: %d rows (category only)", len(rows))
            return rows

    # --- level 3: any published listing ---
    rows = _fresh_query(sb).limit(50).execute().data or []
    log.info("candidates: %d rows (any published, no category match)", len(rows))
    return rows


def _area(d: dict[str, Any] | None) -> float | None:
    if not d:
        return None
    length = d.get("length_cm")
    width = d.get("width_cm")
    if length and width:
        try:
            return float(length) * float(width)
        except (TypeError, ValueError):
            return None
    return None


def _overlap(a: list[str], b: list[str]) -> int:
    return len({x.lower() for x in a} & {x.lower() for x in b})


def _score(product: Product, candidate: dict[str, Any]) -> float:
    mat = _overlap(product.materials, candidate.get("materials") or [])
    col = _overlap(product.colors, candidate.get("colors") or [])
    tag = _overlap(product.tags, candidate.get("tags") or [])

    target_area = _area(product.dimensions.model_dump())
    cand_area = _area(candidate.get("dimensions"))
    dim_sim = 0.0
    if target_area and cand_area:
        denom = max(target_area, cand_area)
        dim_sim = 1.0 - abs(target_area - cand_area) / denom

    return 2.0 * mat + col + 0.5 * tag + dim_sim


def _rerank(product: Product, rows: list[dict[str, Any]], k: int) -> list[dict[str, Any]]:
    scored = sorted(rows, key=lambda r: _score(product, r), reverse=True)
    return scored[:k]


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------
_SYSTEM = (
    "You are a Moroccan handicraft pricing expert. Given a target item and a "
    "list of comparable recent listings (prices in MAD), suggest a fair market "
    "price. Be conservative but realistic; account for materials, dimensions, "
    "region, and condition. Respond with a SINGLE JSON object only — no prose, "
    "no code fences. Schema: "
    '{"suggested": number, "min": number, "max": number, "currency": "MAD", '
    '"confidence": number between 0 and 1, "reasoning": string}.'
)


def _build_user_prompt(product: Product, comps: list[dict[str, Any]]) -> str:
    target = {
        "category": product.category,
        "subcategory": product.subcategory,
        "materials": product.materials,
        "colors": product.colors,
        "dimensions": product.dimensions.model_dump(),
        "origin": product.origin.model_dump(),
        "condition": product.condition,
        "tags": product.tags[:8],
        "title_en": product.title.en,
    }
    slim_comps = [
        {
            "id": str(c["id"]),
            "title_en": c.get("title_en"),
            "materials": c.get("materials") or [],
            "colors": c.get("colors") or [],
            "dimensions": c.get("dimensions") or {},
            "condition": c.get("condition"),
            "origin": c.get("origin") or {},
            "price_mad": float(c.get("price_amount") or 0),
        }
        for c in comps
    ]
    return (
        "TARGET ITEM:\n"
        f"{json.dumps(target, ensure_ascii=False)}\n\n"
        f"COMPARABLES (n={len(slim_comps)}):\n"
        f"{json.dumps(slim_comps, ensure_ascii=False)}\n\n"
        "Return the JSON pricing recommendation now."
    )


def _call_groq(user_msg: str) -> str:
    from groq import Groq

    settings = get_settings()
    client = Groq(api_key=settings.groq_api_key)
    completion = client.chat.completions.create(
        model=settings.groq_primary_model,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.3,
        max_tokens=600,
        response_format={"type": "json_object"},
    )
    return completion.choices[0].message.content or ""


def _fallback(comps: list[dict[str, Any]]) -> PriceRecommendation:
    prices = [float(c.get("price_amount") or 0) for c in comps if c.get("price_amount")]
    if not prices:
        return PriceRecommendation(
            suggested=0,
            min=0,
            max=0,
            confidence=0.0,
            reasoning="No comparable listings found in the catalog yet.",
        )
    suggested = round(statistics.median(prices), 2)
    lo = round(min(prices), 2)
    hi = round(max(prices), 2)
    return PriceRecommendation(
        suggested=suggested,
        min=lo,
        max=hi,
        confidence=0.3,
        reasoning=(
            f"Fallback: median of {len(prices)} comparable listing(s). "
            "AI reasoning was unavailable, so this is a statistical guess only."
        ),
        comparable_ids=[str(c["id"]) for c in comps],
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def recommend(product: Product) -> tuple[PriceRecommendation, list[dict[str, Any]]]:
    """Return ``(recommendation, comparables_used)`` for the given product."""
    settings = get_settings()
    rows = _fetch_candidates(product)
    log.info("recommend: %d candidates fetched for category=%s", len(rows), product.category)
    if not rows:
        return _fallback([]), []

    top = _rerank(product, rows, settings.price_top_k)

    if not settings.groq_api_key:
        log.warning("GROQ_API_KEY missing; using statistical fallback")
        return _fallback(top), top

    try:
        raw = _call_groq(_build_user_prompt(product, top))
        parsed = json.loads(raw)
        rec = PriceRecommendation.model_validate(parsed)
    except (json.JSONDecodeError, PydanticValidationError) as exc:
        log.warning("LLM recommendation parse failed: %s", exc)
        return _fallback(top), top
    except Exception as exc:  # noqa: BLE001 - upstream API errors
        log.error("LLM recommendation call failed: %s", exc)
        return _fallback(top), top

    # Clamp & decorate.
    if rec.min and rec.max and rec.min > rec.max:
        rec.min, rec.max = rec.max, rec.min
    if rec.suggested < rec.min:
        rec.suggested = rec.min
    if rec.max and rec.suggested > rec.max:
        rec.suggested = rec.max
    rec.comparable_ids = [str(c["id"]) for c in top]
    return rec, top
