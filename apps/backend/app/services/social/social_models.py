"""Strict Pydantic contracts for the Social Commerce module.

No ``Any``. Inputs forbid unknown fields so malformed payloads fail
loudly instead of silently dropping data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
)

Platform = Literal["facebook"]
Language = Literal["en", "fr", "ar"]

# Facebook's hard limit for a post message.
FACEBOOK_CAPTION_MAX = 63206
MAX_HASHTAGS = 10


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# --------------------------------------------------------------------------- #
# Generation
# --------------------------------------------------------------------------- #
class SocialGenerationInput(_StrictModel):
    product_title: str = Field(min_length=2, max_length=200)
    marketing_description: str = Field(min_length=10)
    price_mad: str = Field(min_length=1)
    price_usd: str = Field(min_length=1)
    origin: str = Field(min_length=1)
    materials: list[str] = Field(min_length=1)
    target_market: str = Field(min_length=1)

    @field_validator("materials")
    @classmethod
    def _clean_materials(cls, v: list[str]) -> list[str]:
        cleaned = [m.strip() for m in v if m and m.strip()]
        if not cleaned:
            raise ValueError("materials must contain at least one value")
        return cleaned


class LocalizedSocial(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    caption: str = Field(min_length=1)
    cta: str = Field(min_length=1)
    hashtags: list[str] = Field(min_length=1)

    @field_validator("hashtags")
    @classmethod
    def _normalize_hashtags(cls, v: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for raw in v:
            tag = raw.strip().lstrip("#").strip()
            tag = tag.replace(" ", "")
            if not tag:
                continue
            key = tag.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(f"#{tag}")
            if len(out) >= MAX_HASHTAGS:
                break
        if not out:
            raise ValueError("at least one valid hashtag is required")
        return out


class PlatformContent(BaseModel):
    en: LocalizedSocial
    fr: LocalizedSocial
    ar: LocalizedSocial


class SocialContentBundle(BaseModel):
    facebook: PlatformContent

    @field_validator("facebook")
    @classmethod
    def _enforce_facebook_limit(cls, v: PlatformContent) -> PlatformContent:
        for lang in ("en", "fr", "ar"):
            block: LocalizedSocial = getattr(v, lang)
            if len(block.caption) > FACEBOOK_CAPTION_MAX:
                block.caption = block.caption[:FACEBOOK_CAPTION_MAX].rstrip()
        return v


# --------------------------------------------------------------------------- #
# Publishing
# --------------------------------------------------------------------------- #
class FacebookPublishInput(_StrictModel):
    caption: str = Field(min_length=1)
    # The artisan's uploaded photo, as a base64 data URL
    # (``data:image/...;base64,...``). Uploaded to the Page as a real
    # file. When omitted, a text-only Page post is published instead.
    image_data_url: str | None = None
    # Optional public image URL (used by the scheduler, which only has a
    # stored URL). Ignored when ``image_data_url`` is provided.
    image_url: HttpUrl | None = None


class FacebookPublishResult(BaseModel):
    status: Literal["success"] = "success"
    post_id: str


# --------------------------------------------------------------------------- #
# Scheduling
# --------------------------------------------------------------------------- #
class SchedulePostInput(_StrictModel):
    platform: Platform
    scheduled_time: datetime
    image_url: HttpUrl
    caption: str = Field(min_length=1, max_length=FACEBOOK_CAPTION_MAX)

    @field_validator("scheduled_time")
    @classmethod
    def _must_be_future_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("scheduled_time must be timezone-aware (ISO 8601)")
        if v <= datetime.now(timezone.utc):
            raise ValueError("scheduled_time must be in the future")
        return v


class ScheduleResult(BaseModel):
    status: Literal["scheduled"] = "scheduled"
    job_id: str
    platform: Platform
    scheduled_time: datetime


JobStatus = Literal["pending", "published", "failed"]


class ScheduledPost(BaseModel):
    id: str
    platform: Platform
    image_url: str
    caption: str
    scheduled_time: datetime
    status: JobStatus = "pending"
    created_at: datetime
    post_id: str = ""
    error: str = ""
