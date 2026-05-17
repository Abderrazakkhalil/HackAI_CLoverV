"""Typed request/response contracts.

The :class:`Product` mirrors the Hirafi pipeline's rich multilingual
e-commerce schema. The LLM is forced to match this; raw model text is
never trusted (validated + retried in services/llm.py).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SpeechLang = Literal["darija", "amazigh"]


class TranscriptionResult(BaseModel):
    text: str = Field(..., description="Raw transcription (Darija or Amazigh)")
    language: str = "ar-MA"
    source: str = Field("moulsot", description="moulsot | tamazight-nlp")


class LocalizedText(BaseModel):
    en: str = ""
    fr: str = ""
    ar: str = ""


class Price(BaseModel):
    amount: float = 0
    currency: str = "MAD"
    price_usd_estimate: float = 0.0
    negotiable: bool = True


class Dimensions(BaseModel):
    length_cm: float | None = None
    width_cm: float | None = None
    height_cm: float | None = None
    weight_kg: float | None = None


class Origin(BaseModel):
    country: str = "Morocco"
    region: str | None = None
    technique: str | None = None


class Shipping(BaseModel):
    local_available: bool = True
    international_available: bool = False
    fragile: bool = False


class Product(BaseModel):
    """Frontend-ready, marketplace-quality multilingual listing."""

    title: LocalizedText
    description: LocalizedText
    category: str = "Handmade"
    subcategory: str | None = None
    tags: list[str] = Field(default_factory=list)
    price: Price = Field(default_factory=Price)
    dimensions: Dimensions = Field(default_factory=Dimensions)
    materials: list[str] = Field(default_factory=list)
    colors: list[str] = Field(default_factory=list)
    origin: Origin = Field(default_factory=Origin)
    condition: str = "handmade-new"
    quantity_available: int | None = None
    lead_time_days: int | None = None
    shipping: Shipping = Field(default_factory=Shipping)
    artisan_notes: str | None = None
    raw_transcript: str = ""
    confidence_score: float = 0.0
    missing_fields: list[str] = Field(default_factory=list)


class Artisan(BaseModel):
    """Artisan profile captured at sign-up, attached to every post."""

    full_name: str = ""
    city_region: str = ""
    phone: str = ""


class Meta(BaseModel):
    pipeline_version: str
    asr_model: str
    asr_provider: str
    llm_model: str
    processed_at: str
    audio_filename: str
    inference_ms: int


class GenerateRequest(BaseModel):
    transcription: str = Field(..., min_length=1)


class ProcessResponse(BaseModel):
    """Full-pipeline response returned to the frontend."""

    product: Product
    meta: Meta
    transcription: TranscriptionResult
    artisan: Artisan | None = None
    image_data_url: str | None = None


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
