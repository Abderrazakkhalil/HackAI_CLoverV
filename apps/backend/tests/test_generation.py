"""Tests for social content generation via Groq."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError as PydanticValidationError
from unittest.mock import patch, MagicMock

from app.services.social.social_generator import (
    _build_user_prompt,
    _strip_fences,
    _generate_with_model,
    generate_social_content,
)
from app.services.social.social_models import (
    SocialGenerationInput,
    SocialContentBundle,
    LocalizedSocial,
    PlatformContent,
)
from app.services.social.social_exceptions import (
    SocialConfigError,
    SocialGenerationError,
)


def test_strip_fences_plain():
    """Plain JSON should pass through."""
    json_str = '{"facebook": {}}'
    assert _strip_fences(json_str) == json_str


def test_strip_fences_markdown():
    """Remove markdown code fences."""
    raw = '```json\n{"facebook": {}}\n```'
    assert _strip_fences(raw) == '{"facebook": {}}'


def test_strip_fences_mixed():
    """Handle mixed whitespace around fences."""
    raw = '```\n  {"data": 123}  \n```'
    assert _strip_fences(raw).strip() == '{"data": 123}'


@pytest.fixture
def valid_generation_input() -> SocialGenerationInput:
    """Valid social generation input."""
    return SocialGenerationInput(
        product_title="Handmade Ceramic Bowl",
        marketing_description="Beautiful hand-thrown ceramic bowl from Fez.",
        price_mad="450",
        price_usd="45",
        origin="Fez, Morocco",
        materials=["ceramic", "glaze"],
        target_market="EU",
    )


def test_build_user_prompt(valid_generation_input):
    """User prompt includes all product details."""
    prompt = _build_user_prompt(valid_generation_input)
    assert "Handmade Ceramic Bowl" in prompt
    assert "450" in prompt
    assert "Fez, Morocco" in prompt
    assert "ceramic" in prompt
    assert "target_market" in prompt
    assert "Return JSON with EXACTLY this shape" in prompt


@pytest.fixture
def valid_social_bundle_json() -> str:
    """Valid JSON response from Groq."""
    return json.dumps({
        "facebook": {
            "en": {
                "caption": "This beautiful ceramic bowl is handcrafted.",
                "cta": "Learn more",
                "hashtags": ["#ceramics", "#artisan"],
            },
            "fr": {
                "caption": "Ce magnifique bol en céramique est fait à la main.",
                "cta": "En savoir plus",
                "hashtags": ["#ceramique", "#artisan"],
            },
            "ar": {
                "caption": "هذا الوعاء الجميل مصنوع يدويًا.",
                "cta": "معرفة المزيد",
                "hashtags": ["#سيراميك", "#حرفي"],
            },
        },
    })


@pytest.mark.asyncio
async def test_generate_with_model_success(
    valid_generation_input, valid_social_bundle_json, monkeypatch
):
    """Successfully generate social content from Groq."""
    mock_call = MagicMock(return_value=valid_social_bundle_json)
    monkeypatch.setattr("app.services.social.social_generator._call_groq", mock_call)

    result = _generate_with_model("llama-4-scout", valid_generation_input)

    assert isinstance(result, SocialContentBundle)
    assert result.facebook.en.caption == (
        "This beautiful ceramic bowl is handcrafted."
    )
    assert result.facebook.fr.cta == "En savoir plus"
    assert mock_call.called


@pytest.mark.asyncio
async def test_generate_with_model_with_fences(
    valid_generation_input, valid_social_bundle_json, monkeypatch
):
    """Handle Groq response with code fences."""
    fenced = f"```json\n{valid_social_bundle_json}\n```"
    mock_call = MagicMock(return_value=fenced)
    monkeypatch.setattr("app.services.social.social_generator._call_groq", mock_call)

    result = _generate_with_model("llama-4-scout", valid_generation_input)

    assert isinstance(result, SocialContentBundle)
    assert result.facebook.en.caption == (
        "This beautiful ceramic bowl is handcrafted."
    )


@pytest.mark.asyncio
async def test_generate_with_model_exhausts_retries(
    valid_generation_input, monkeypatch
):
    """Raise ValueError when retries exhausted."""
    mock_call = MagicMock(return_value='{"invalid": "always"}')
    monkeypatch.setattr("app.services.social.social_generator._call_groq", mock_call)

    with pytest.raises(ValueError, match="invalid social content after retries"):
        _generate_with_model("llama-4-scout", valid_generation_input)


@pytest.mark.asyncio
async def test_generate_social_content_success(
    valid_generation_input, valid_social_bundle_json, monkeypatch
):
    """Successfully generate via primary model."""
    mock_call = MagicMock(return_value=valid_social_bundle_json)
    monkeypatch.setattr("app.services.social.social_generator._call_groq", mock_call)
    monkeypatch.setenv("GROQ_API_KEY", "test-key-123")

    result = generate_social_content(valid_generation_input)

    assert isinstance(result, SocialContentBundle)
    assert result.facebook.en.caption


@pytest.mark.asyncio
async def test_generate_social_content_fallback_model(
    valid_generation_input, valid_social_bundle_json, monkeypatch
):
    """Fall back to secondary model on primary failure."""
    call_count = 0

    def mock_call(model, system, user):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Primary model timeout")
        return valid_social_bundle_json

    monkeypatch.setattr("app.services.social.social_generator._call_groq", mock_call)
    monkeypatch.setenv("GROQ_API_KEY", "test-key-123")

    result = generate_social_content(valid_generation_input)

    assert isinstance(result, SocialContentBundle)
    assert call_count == 2


def test_generation_input_validation():
    """Validate input constraints."""
    # Title too short
    with pytest.raises(PydanticValidationError):
        SocialGenerationInput(
            product_title="X",  # min_length=2
            marketing_description="Valid description",
            price_mad="100",
            price_usd="10",
            origin="Morocco",
            materials=["test"],
            target_market="EU",
        )

    # Description too short
    with pytest.raises(PydanticValidationError):
        SocialGenerationInput(
            product_title="Valid Title",
            marketing_description="short",  # min_length=10
            price_mad="100",
            price_usd="10",
            origin="Morocco",
            materials=["test"],
            target_market="EU",
        )

    # Materials empty after stripping
    with pytest.raises(PydanticValidationError):
        SocialGenerationInput(
            product_title="Valid Title",
            marketing_description="Valid description",
            price_mad="100",
            price_usd="10",
            origin="Morocco",
            materials=[""],  # will be filtered out
            target_market="EU",
        )


def test_generation_input_forbids_extra_fields():
    """Unknown fields should raise validation error."""
    with pytest.raises(PydanticValidationError):
        SocialGenerationInput(
            product_title="Valid Title",
            marketing_description="Valid description",
            price_mad="100",
            price_usd="10",
            origin="Morocco",
            materials=["test"],
            target_market="EU",
            unknown_field="should fail",
        )
