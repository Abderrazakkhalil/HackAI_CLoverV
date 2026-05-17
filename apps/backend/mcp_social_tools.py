"""Social Commerce MCP tools.

Registered onto the shared FastMCP instance by ``mcp_server.py``. Same
service layer as the REST API. Tools never raise to the agent — typed
failures are returned as the structured error envelope.
"""

from __future__ import annotations

import asyncio

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError as PydanticValidationError

from app.logging_conf import get_logger
from app.services.social.analytics_service import analytics_provider
from app.services.social.facebook_service import (
    publish_facebook_post as fb_publish,
)
from app.services.social.scheduler_service import scheduler_service
from app.services.social.social_exceptions import SocialError
from app.services.social.social_generator import generate_social_content
from app.services.social.social_models import (
    FacebookPublishInput,
    Platform,
    SchedulePostInput,
    SocialGenerationInput,
)

log = get_logger("hackai.mcp.social")


def _envelope(code: str, message: str, details: str) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


def _bad_input(exc: PydanticValidationError) -> dict:
    return _envelope("invalid_input", "Input failed validation.", str(exc))


def register(mcp: FastMCP) -> None:
    """Attach the Social Commerce tools to ``mcp``."""

    @mcp.tool()
    async def generate_social_post(
        product_title: str,
        marketing_description: str,
        price_mad: str,
        price_usd: str,
        origin: str,
        materials: list[str],
        target_market: str,
    ) -> dict:
        """Generate EN/FR/AR Facebook captions, CTAs, hashtags."""
        try:
            data = SocialGenerationInput(
                product_title=product_title,
                marketing_description=marketing_description,
                price_mad=price_mad,
                price_usd=price_usd,
                origin=origin,
                materials=materials,
                target_market=target_market,
            )
        except PydanticValidationError as exc:
            return _bad_input(exc)
        try:
            bundle = await asyncio.to_thread(generate_social_content, data)
            return bundle.model_dump()
        except SocialError as exc:
            return exc.to_envelope()

    @mcp.tool()
    async def publish_facebook_post(image_url: str, caption: str) -> dict:
        """Publish an image + caption to a Facebook Page via Graph API."""
        try:
            data = FacebookPublishInput(image_url=image_url, caption=caption)
        except PydanticValidationError as exc:
            return _bad_input(exc)
        try:
            return (await fb_publish(data)).model_dump()
        except SocialError as exc:
            return exc.to_envelope()

    @mcp.tool()
    async def schedule_post(
        platform: Platform,
        scheduled_time: str,
        image_url: str,
        caption: str,
    ) -> dict:
        """Schedule a post (ISO 8601 UTC time) for later publishing."""
        try:
            data = SchedulePostInput(
                platform=platform,
                scheduled_time=scheduled_time,
                image_url=image_url,
                caption=caption,
            )
        except PydanticValidationError as exc:
            return _bad_input(exc)
        try:
            return scheduler_service.schedule(data).model_dump(mode="json")
        except SocialError as exc:
            return exc.to_envelope()

    @mcp.tool()
    async def get_campaign_analytics(platform: Platform, post_id: str) -> dict:
        """Engagement metrics for a published post (not implemented yet)."""
        try:
            return await analytics_provider.get_campaign_analytics(
                platform=platform, post_id=post_id
            )
        except SocialError as exc:
            return exc.to_envelope()
