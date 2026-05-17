"""Tests for Facebook publishing via Meta Graph API."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from pydantic import ValidationError as PydanticValidationError

from app.services.social.facebook_service import publish_facebook_post
from app.services.social.social_models import FacebookPublishInput, FacebookPublishResult
from app.services.social.social_exceptions import (
    FacebookPublishError,
    SocialConfigError,
)
from tests._social_fakes import configure_meta


@pytest.fixture
def valid_facebook_input() -> FacebookPublishInput:
    """Valid Facebook publish input."""
    return FacebookPublishInput(
        image_url="https://example.com/image.jpg",
        caption="Beautiful handcrafted ceramic bowl from Fez! "
                "This piece tells the story of generations of artisans...",
    )


@pytest.mark.asyncio
async def test_publish_facebook_success(valid_facebook_input, monkeypatch):
    """Successfully publish to Facebook."""
    configure_meta(monkeypatch)

    async def mock_graph_request(method, endpoint, **kwargs):
        return {"post_id": "post_123"}

    monkeypatch.setattr(
        "app.services.social.facebook_service.graph_request",
        mock_graph_request,
    )

    result = await publish_facebook_post(valid_facebook_input)

    assert isinstance(result, FacebookPublishResult)
    assert result.status == "success"
    assert result.post_id == "post_123"


@pytest.mark.asyncio
async def test_publish_facebook_fallback_id_field(valid_facebook_input, monkeypatch):
    """Handle response with 'id' field instead of 'post_id'."""
    configure_meta(monkeypatch)

    async def mock_graph_request(method, endpoint, **kwargs):
        return {"id": "post_789"}  # Alternate field name

    monkeypatch.setattr(
        "app.services.social.facebook_service.graph_request",
        mock_graph_request,
    )

    result = await publish_facebook_post(valid_facebook_input)

    assert result.post_id == "post_789"


@pytest.mark.asyncio
async def test_publish_facebook_no_post_id(valid_facebook_input, monkeypatch):
    """Raise FacebookPublishError when post ID is missing."""
    configure_meta(monkeypatch)

    async def mock_graph_request(method, endpoint, **kwargs):
        return {}  # No 'post_id' or 'id' field

    monkeypatch.setattr(
        "app.services.social.facebook_service.graph_request",
        mock_graph_request,
    )

    with pytest.raises(FacebookPublishError):
        await publish_facebook_post(valid_facebook_input)


@pytest.mark.asyncio
async def test_publish_facebook_require_credentials(monkeypatch):
    """Raise SocialConfigError when Facebook page ID is missing."""
    from app.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "meta_access_token", "token", raising=False)
    monkeypatch.setattr(s, "facebook_page_id", "", raising=False)  # Empty

    valid_input = FacebookPublishInput(
        image_url="https://example.com/image.jpg",
        caption="Test caption for Facebook",
    )

    with pytest.raises(SocialConfigError):
        await publish_facebook_post(valid_input)


def test_facebook_publish_input_validation():
    """Validate Facebook input constraints."""
    # Valid input
    input_ok = FacebookPublishInput(
        image_url="https://example.com/image.jpg",
        caption="Valid caption",
    )
    assert input_ok.caption == "Valid caption"

    # Caption empty
    with pytest.raises(PydanticValidationError):
        FacebookPublishInput(
            image_url="https://example.com/image.jpg",
            caption="",
        )

    # Invalid URL
    with pytest.raises(PydanticValidationError):
        FacebookPublishInput(
            image_url="not-a-url",  # type: ignore
            caption="Valid caption",
        )


def test_facebook_publish_input_forbids_extra_fields():
    """Unknown fields should raise validation error."""
    with pytest.raises(PydanticValidationError):
        FacebookPublishInput(
            image_url="https://example.com/image.jpg",
            caption="Valid caption",
            unknown_field="should fail",
        )


@pytest.mark.asyncio
async def test_publish_facebook_long_caption(monkeypatch):
    """Facebook allows very long captions."""
    configure_meta(monkeypatch)

    long_caption = "x" * 5000

    input_long = FacebookPublishInput(
        image_url="https://example.com/image.jpg",
        caption=long_caption,
    )

    async def mock_graph_request(method, endpoint, **kwargs):
        return {"post_id": "post_long"}

    monkeypatch.setattr(
        "app.services.social.facebook_service.graph_request",
        mock_graph_request,
    )

    result = await publish_facebook_post(input_long)
    assert result.post_id == "post_long"


@pytest.mark.asyncio
async def test_publish_facebook_graph_request_error(valid_facebook_input, monkeypatch):
    """Propagate graph_request exceptions."""
    configure_meta(monkeypatch)

    async def mock_graph_request(method, endpoint, **kwargs):
        raise Exception("API rate limit exceeded")

    monkeypatch.setattr(
        "app.services.social.facebook_service.graph_request",
        mock_graph_request,
    )

    with pytest.raises(Exception, match="rate limit"):
        await publish_facebook_post(valid_facebook_input)


def test_facebook_publish_result():
    """Validate FacebookPublishResult structure."""
    result = FacebookPublishResult(post_id="post_456")

    assert result.status == "success"
    assert result.post_id == "post_456"


@pytest.mark.asyncio
async def test_publish_facebook_caption_whitespace(monkeypatch):
    """Ensure captions with extra whitespace are handled."""
    configure_meta(monkeypatch)

    input_with_spaces = FacebookPublishInput(
        image_url="https://example.com/image.jpg",
        caption="  Caption with spaces  \n\n  Multiple lines  ",
    )

    async def mock_graph_request(method, endpoint, **kwargs):
        return {"post_id": "post_spaces"}

    monkeypatch.setattr(
        "app.services.social.facebook_service.graph_request",
        mock_graph_request,
    )

    result = await publish_facebook_post(input_with_spaces)
    assert result.post_id == "post_spaces"


@pytest.mark.asyncio
async def test_publish_facebook_integer_post_id(monkeypatch):
    """Handle integer post IDs returned from API."""
    configure_meta(monkeypatch)

    async def mock_graph_request(method, endpoint, error_cls=None, data=None):
        return {"post_id": 12345}  # Integer instead of string

    monkeypatch.setattr(
        "app.services.social.facebook_service.graph_request",
        mock_graph_request,
    )

    valid_input = FacebookPublishInput(
        image_url="https://example.com/image.jpg",
        caption="Test",
    )

    result = await publish_facebook_post(valid_input)
    assert result.post_id == "12345"


@pytest.mark.asyncio
async def test_publish_facebook_text_only(monkeypatch):
    """No image → text-only post via the /feed edge with `message`."""
    configure_meta(monkeypatch)
    seen: dict = {}

    async def mock_graph_request(method, endpoint, **kwargs):
        seen["endpoint"] = endpoint
        seen["data"] = kwargs.get("data")
        seen["files"] = kwargs.get("files")
        return {"id": "feed_1"}

    monkeypatch.setattr(
        "app.services.social.facebook_service.graph_request",
        mock_graph_request,
    )

    result = await publish_facebook_post(
        FacebookPublishInput(caption="Just a text post")
    )

    assert result.post_id == "feed_1"
    assert seen["endpoint"].endswith("/feed")
    assert seen["data"] == {"message": "Just a text post"}
    assert seen["files"] is None


@pytest.mark.asyncio
async def test_publish_facebook_uploaded_photo(monkeypatch):
    """A data-URL image → uploaded as real file bytes to /photos."""
    configure_meta(monkeypatch)
    seen: dict = {}

    async def mock_graph_request(method, endpoint, **kwargs):
        seen["endpoint"] = endpoint
        seen["files"] = kwargs.get("files")
        seen["data"] = kwargs.get("data")
        return {"post_id": "photo_1"}

    monkeypatch.setattr(
        "app.services.social.facebook_service.graph_request",
        mock_graph_request,
    )

    # 1x1 transparent PNG.
    png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0l"
        "EQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    result = await publish_facebook_post(
        FacebookPublishInput(
            caption="With photo",
            image_data_url=f"data:image/png;base64,{png_b64}",
        )
    )

    assert result.post_id == "photo_1"
    assert seen["endpoint"].endswith("/photos")
    assert "source" in seen["files"]
    fname, raw, mime = seen["files"]["source"]
    assert mime == "image/png"
    assert isinstance(raw, bytes) and len(raw) > 0
    assert seen["data"] == {"caption": "With photo", "published": "true"}


@pytest.mark.asyncio
async def test_publish_facebook_bad_data_url(monkeypatch):
    """A malformed data URL fails loudly, not silently."""
    configure_meta(monkeypatch)

    async def mock_graph_request(method, endpoint, **kwargs):
        return {"post_id": "should_not_be_called"}

    monkeypatch.setattr(
        "app.services.social.facebook_service.graph_request",
        mock_graph_request,
    )

    with pytest.raises(FacebookPublishError):
        await publish_facebook_post(
            FacebookPublishInput(
                caption="Bad image",
                image_data_url="not-a-data-url",
            )
        )
