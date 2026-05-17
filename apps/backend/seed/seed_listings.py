"""Seed script — loads 30 Moroccan rug listings into Supabase.

Usage (from apps/backend/):
    python -m seed.seed_listings

Idempotent: uses ``seed_key`` unique column to upsert, so re-running is safe.
Requires a seed user (created automatically if missing).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Allow running as `python -m seed.seed_listings` from apps/backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.supabase_client import get_supabase

FIXTURES = Path(__file__).parent / "fixtures" / "rugs.json"


def _get_or_create_seed_user(sb, settings) -> str:
    """Return the UUID of the seed seller, creating the account if needed."""
    email = settings.seed_user_email
    password = settings.seed_user_password

    # Try to find existing user via admin API.
    try:
        resp = sb.auth.admin.list_users()
        users = getattr(resp, "users", []) or []
        for u in users:
            if getattr(u, "email", None) == email:
                print(f"  Seed user already exists: {u.id}")
                return u.id
    except Exception as exc:
        print(f"  Warning: could not list users ({exc}); will try to create.")

    # Create the seed user.
    try:
        result = sb.auth.admin.create_user(
            {"email": email, "password": password, "email_confirm": True}
        )
        user = result.user
        print(f"  Seed user created: {user.id}")
        # Upsert profile row.
        sb.table("profiles").upsert(
            {
                "id": user.id,
                "full_name": "Seed Artisan",
                "city_region": "Marrakech",
                "phone": "+212600000000",
            }
        ).execute()
        return user.id
    except Exception as exc:
        raise RuntimeError(f"Could not create seed user: {exc}") from exc


def seed() -> None:
    settings = get_settings()

    if not settings.supabase_url or not settings.supabase_service_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        sys.exit(1)

    sb = get_supabase()
    print("Connecting to Supabase…")

    print("Resolving seed user…")
    seller_id = _get_or_create_seed_user(sb, settings)

    print(f"Loading fixtures from {FIXTURES}…")
    listings: list[dict] = json.loads(FIXTURES.read_text(encoding="utf-8"))

    upserted = 0
    for listing in listings:
        row = {
            "seller_id": seller_id,
            "status": "published",
            "seed_key": listing["seed_key"],
            "title_en": listing.get("title_en", ""),
            "title_fr": listing.get("title_fr", ""),
            "title_ar": listing.get("title_ar", ""),
            "description_en": listing.get("description_en", ""),
            "description_fr": listing.get("description_fr", ""),
            "description_ar": listing.get("description_ar", ""),
            "category": listing.get("category", "Rugs & Carpets"),
            "subcategory": listing.get("subcategory"),
            "tags": listing.get("tags", []),
            "materials": listing.get("materials", []),
            "colors": listing.get("colors", []),
            "images": [],
            "price_amount": listing.get("price_amount", 0),
            "price_currency": listing.get("price_currency", "MAD"),
            "price_usd_estimate": listing.get("price_usd_estimate", 0),
            "price_negotiable": listing.get("price_negotiable", True),
            "price_source": listing.get("price_source", "user"),
            "dimensions": listing.get("dimensions", {}),
            "origin": listing.get("origin", {}),
            "shipping": {"local_available": True, "international_available": False, "fragile": False},
            "condition": listing.get("condition", "handmade-new"),
            "artisan_notes": listing.get("artisan_notes"),
            "raw_transcript": "",
        }
        sb.table("listings").upsert(row, on_conflict="seed_key").execute()
        upserted += 1
        print(f"  [{upserted:02d}/{len(listings)}] {listing['seed_key']} — {listing.get('title_en', '')[:60]}")

    print(f"\nDone. Upserted {upserted} listings (seller_id={seller_id}).")


if __name__ == "__main__":
    seed()
