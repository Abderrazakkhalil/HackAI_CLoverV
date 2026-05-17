"""HTTP API consumed by the Hirfati frontend."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import ValidationError as PydanticValidationError

from .config import get_settings
from .deps import get_current_user
from .errors import ValidationError
from .logging_conf import get_logger
from .schemas import Artisan, GenerateRequest, ProcessResponse, Product
from .schemas_db import (
    AuthResponse,
    AuthUser,
    ListingCreate,
    ListingFilters,
    ListingOut,
    LoginRequest,
    RecommendPriceRequest,
    RecommendPriceResponse,
    SignupRequest,
)
from .services.auth import login as auth_login
from .services.auth import signup as auth_signup
from .services.listings import create_listing, get_listing, list_listings
from .services.llm import generate_product
from .services.orchestrator import run_pipeline
from .services.price_recommendation import recommend as recommend_price

log = get_logger("hackai.api")
router = APIRouter(prefix="/api")


@router.get("/health")
async def health() -> dict:
    s = get_settings()
    return {
        "status": "ok",
        "pipeline_version": s.pipeline_version,
        "providers": {
            "moulsot": bool(s.hf_token),
            "groq": bool(s.groq_api_key),
            "supabase": bool(s.supabase_url and s.supabase_service_key),
        },
    }


_ALLOWED_SPEECH_LANGS = {"darija", "amazigh"}


@router.post("/process", response_model=ProcessResponse)
async def process(
    audio: UploadFile = File(...),
    image: UploadFile | None = File(default=None),
    artisan: str | None = Form(default=None),
    speech_lang: str = Form(default="darija"),
) -> ProcessResponse:
    """Full pipeline: audio (+ optional image, + artisan) -> listing."""
    log.info(
        "POST /api/process: audio=%s, image=%s, speech_lang=%s",
        audio.filename,
        image.filename if image else None,
        speech_lang,
    )

    if speech_lang not in _ALLOWED_SPEECH_LANGS:
        log.error("Invalid speech_lang: %s", speech_lang)
        raise ValidationError(
            f"Unsupported speech_lang: {speech_lang!r}. "
            f"Expected one of {sorted(_ALLOWED_SPEECH_LANGS)}."
        )

    audio_bytes = await audio.read()
    image_bytes = await image.read() if image is not None else None
    log.info(
        "Files read: audio_bytes=%d, image_bytes=%s",
        len(audio_bytes),
        len(image_bytes) if image_bytes else None,
    )

    artisan_obj: Artisan | None = None
    if artisan:
        try:
            artisan_obj = Artisan.model_validate(json.loads(artisan))
        except (json.JSONDecodeError, PydanticValidationError) as exc:
            log.error("Invalid artisan JSON: %s", exc)
            raise ValidationError(
                "Invalid artisan profile.", detail=str(exc)
            ) from exc

    log.info("Pipeline starting...")
    return await run_pipeline(
        audio_bytes=audio_bytes,
        audio_filename=audio.filename or "audio.webm",
        audio_content_type=audio.content_type,
        image_bytes=image_bytes or None,
        image_filename=image.filename if image else None,
        image_content_type=image.content_type if image else None,
        artisan=artisan_obj,
        speech_lang=speech_lang,  # type: ignore[arg-type]
    )


@router.post("/generate", response_model=Product)
async def generate(req: GenerateRequest) -> Product:
    """Text-only path (useful for testing without recording audio)."""
    if not req.transcription.strip():
        raise ValidationError("Transcription text is required.")
    product, label = generate_product(req.transcription)
    log.info("Listing extracted via %s (text endpoint)", label)
    return product


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@router.post("/auth/signup", response_model=AuthResponse)
async def signup(payload: SignupRequest) -> AuthResponse:
    log.info("POST /api/auth/signup email=%s", payload.email)
    return auth_signup(payload)


@router.post("/auth/login", response_model=AuthResponse)
async def login(payload: LoginRequest) -> AuthResponse:
    log.info("POST /api/auth/login email=%s", payload.email)
    return auth_login(payload)


@router.get("/auth/me", response_model=AuthUser)
async def me(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    return user


# ---------------------------------------------------------------------------
# Listings
# ---------------------------------------------------------------------------
@router.get("/listings", response_model=list[ListingOut])
async def listings_index(
    category: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ListingOut]:
    return list_listings(ListingFilters(category=category, limit=limit, offset=offset))


@router.get("/listings/{listing_id}", response_model=ListingOut)
async def listing_detail(listing_id: str) -> ListingOut:
    listing = get_listing(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found.")
    return listing


@router.post("/listings", response_model=ListingOut, status_code=201)
async def listings_create(
    payload: ListingCreate,
    user: AuthUser = Depends(get_current_user),
) -> ListingOut:
    return create_listing(
        seller_id=user.id,
        product=payload.product,
        price_source=payload.price_source,
        image_url=payload.image_url,
        status=payload.status,
    )


# ---------------------------------------------------------------------------
# Price recommendation
# ---------------------------------------------------------------------------
@router.post("/recommend-price", response_model=RecommendPriceResponse)
async def recommend_price_route(
    payload: RecommendPriceRequest,
    user: AuthUser = Depends(get_current_user),
) -> RecommendPriceResponse:
    rec, comps = recommend_price(payload.product)
    return RecommendPriceResponse(
        recommendation=rec,
        comparables=[
            {
                "id": str(c["id"]),
                "title_en": c.get("title_en"),
                "price_mad": float(c.get("price_amount") or 0),
                "materials": c.get("materials") or [],
            }
            for c in comps
        ],
    )
