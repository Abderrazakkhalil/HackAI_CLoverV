"""Request/response DTOs for the Supabase-backed endpoints.

Kept separate from :mod:`schemas` so the pipeline contracts stay focused
on the AI extraction surface.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, EmailStr, Field

from .schemas import PriceRecommendation, PriceSource, Product


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)
    full_name: str = ""
    city_region: str = ""
    phone: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthUser(BaseModel):
    id: str
    email: str | None = None
    full_name: str = ""
    city_region: str = ""
    phone: str = ""


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None
    user: AuthUser


# ---------------------------------------------------------------------------
# Listings
# ---------------------------------------------------------------------------
class ListingCreate(BaseModel):
    """Payload for publishing a listing (sent from the frontend Publish button)."""

    product: Product
    price_source: PriceSource = "user"
    image_url: str | None = None
    status: str = "published"


class ListingOut(BaseModel):
    """Full listing row returned to the frontend."""

    id: str
    seller_id: str
    status: str
    product: Product
    price_source: PriceSource
    image_url: str | None = None
    created_at: str
    updated_at: str


class ListingFilters(BaseModel):
    category: str | None = None
    city_region: str | None = None
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


# ---------------------------------------------------------------------------
# Price recommendation
# ---------------------------------------------------------------------------
class RecommendPriceRequest(BaseModel):
    """Partial product used to ask for a price suggestion."""

    product: Product


class RecommendPriceResponse(BaseModel):
    recommendation: PriceRecommendation
    comparables: list[dict[str, Any]] = Field(default_factory=list)
