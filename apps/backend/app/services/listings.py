"""Listing persistence — maps the rich ``Product`` schema to Supabase rows.

Localized text fields are flattened (``title_en``, ``title_fr``, ``title_ar``);
``dimensions``, ``origin``, and ``shipping`` are stored as JSONB.
"""

from __future__ import annotations

from typing import Any

from ..errors import HackAIError
from ..logging_conf import get_logger
from ..schemas import (
    Dimensions,
    LocalizedText,
    Origin,
    Price,
    Product,
    Shipping,
)
from ..schemas_db import ListingFilters, ListingOut, PriceSource
from ..supabase_client import get_supabase

log = get_logger("hackai.listings")


class ListingError(HackAIError):
    status_code = 500
    message = "Listing operation failed."


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------
def _product_to_row(
    product: Product,
    seller_id: str,
    price_source: PriceSource,
    image_url: str | None,
    status: str,
    seed_key: str | None = None,
) -> dict[str, Any]:
    images = [image_url] if image_url else []
    return {
        "seller_id": seller_id,
        "status": status,
        "title_en": product.title.en,
        "title_fr": product.title.fr,
        "title_ar": product.title.ar,
        "description_en": product.description.en,
        "description_fr": product.description.fr,
        "description_ar": product.description.ar,
        "category": product.category,
        "subcategory": product.subcategory,
        "tags": product.tags,
        "materials": product.materials,
        "colors": product.colors,
        "images": images,
        "price_amount": float(product.price.amount or 0),
        "price_currency": product.price.currency,
        "price_usd_estimate": float(product.price.price_usd_estimate or 0),
        "price_negotiable": product.price.negotiable,
        "price_source": price_source,
        "dimensions": product.dimensions.model_dump(),
        "origin": product.origin.model_dump(),
        "shipping": product.shipping.model_dump(),
        "condition": product.condition,
        "quantity_available": product.quantity_available,
        "lead_time_days": product.lead_time_days,
        "artisan_notes": product.artisan_notes,
        "raw_transcript": product.raw_transcript,
        "seed_key": seed_key,
    }


def _row_to_product(row: dict[str, Any]) -> Product:
    return Product(
        title=LocalizedText(
            en=row.get("title_en", ""),
            fr=row.get("title_fr", ""),
            ar=row.get("title_ar", ""),
        ),
        description=LocalizedText(
            en=row.get("description_en", ""),
            fr=row.get("description_fr", ""),
            ar=row.get("description_ar", ""),
        ),
        category=row.get("category") or "Handmade",
        subcategory=row.get("subcategory"),
        tags=row.get("tags") or [],
        price=Price(
            amount=float(row.get("price_amount") or 0),
            currency=row.get("price_currency") or "MAD",
            price_usd_estimate=float(row.get("price_usd_estimate") or 0),
            negotiable=bool(row.get("price_negotiable", True)),
        ),
        dimensions=Dimensions(**(row.get("dimensions") or {})),
        materials=row.get("materials") or [],
        colors=row.get("colors") or [],
        origin=Origin(**(row.get("origin") or {})),
        condition=row.get("condition") or "handmade-new",
        quantity_available=row.get("quantity_available"),
        lead_time_days=row.get("lead_time_days"),
        shipping=Shipping(**(row.get("shipping") or {})),
        artisan_notes=row.get("artisan_notes"),
        raw_transcript=row.get("raw_transcript") or "",
    )


def _row_to_out(row: dict[str, Any]) -> ListingOut:
    images = row.get("images") or []
    return ListingOut(
        id=str(row["id"]),
        seller_id=str(row["seller_id"]),
        status=row.get("status", "published"),
        product=_row_to_product(row),
        price_source=row.get("price_source") or "user",
        image_url=images[0] if images else None,
        created_at=str(row.get("created_at", "")),
        updated_at=str(row.get("updated_at", "")),
    )


# ---------------------------------------------------------------------------
# Public CRUD
# ---------------------------------------------------------------------------
def create_listing(
    seller_id: str,
    product: Product,
    price_source: PriceSource = "user",
    image_url: str | None = None,
    status: str = "published",
) -> ListingOut:
    sb = get_supabase()
    row = _product_to_row(product, seller_id, price_source, image_url, status)
    try:
        resp = sb.table("listings").insert(row).execute()
    except Exception as exc:  # noqa: BLE001
        log.error("Insert listing failed: %s", exc)
        raise ListingError(detail=str(exc)) from exc

    if not resp.data:
        raise ListingError("Listing was not created.")
    return _row_to_out(resp.data[0])


def list_listings(filters: ListingFilters) -> list[ListingOut]:
    sb = get_supabase()
    q = sb.table("listings").select("*").eq("status", "published")
    if filters.category:
        q = q.eq("category", filters.category)
    rows = (
        q.order("created_at", desc=True)
        .range(filters.offset, filters.offset + filters.limit - 1)
        .execute()
        .data
        or []
    )
    return [_row_to_out(r) for r in rows]


def get_listing(listing_id: str) -> ListingOut | None:
    sb = get_supabase()
    rows = (
        sb.table("listings").select("*").eq("id", listing_id).limit(1).execute().data
        or []
    )
    return _row_to_out(rows[0]) if rows else None
