import json

import pytest
from pydantic import ValidationError as PydanticError

from app.schemas import Product
from app.services.llm import _strip_fences, _to_product


def test_strip_plain_json():
    assert _strip_fences('{"a": 1}') == '{"a": 1}'


def test_strip_code_fence():
    raw = '```json\n{"a": 1}\n```'
    assert json.loads(_strip_fences(raw)) == {"a": 1}


VALID = {
    "product": {
        "title": {"en": "Cedar Box", "fr": "Boîte en cèdre", "ar": "صندوق"},
        "description": {
            "en": "A hand-carved cedar keepsake box.",
            "fr": "Une boîte en cèdre sculptée à la main.",
            "ar": "صندوق خشبي منحوت يدويًا.",
        },
        "category": "Woodwork",
        "tags": ["cedar box", "moroccan woodwork"],
        "price": {
            "amount": 600,
            "currency": "MAD",
            "price_usd_estimate": 59.4,
            "negotiable": True,
        },
        "materials": ["cedar wood"],
        "colors": ["brown"],
        "origin": {
            "country": "Morocco",
            "region": "Essaouira",
            "technique": "hand carving",
        },
        "condition": "handmade-new",
        "confidence_score": 0.9,
        "missing_fields": [],
    }
}


def test_to_product_valid():
    p = _to_product(VALID, "raw darija here")
    assert p.title.en == "Cedar Box"
    assert p.price.currency == "MAD"
    # transcript is forced to the authoritative value
    assert p.raw_transcript == "raw darija here"


def test_to_product_accepts_unwrapped():
    p = _to_product(VALID["product"], "t")
    assert p.category == "Woodwork"


def test_product_requires_title_and_description():
    with pytest.raises(PydanticError):
        Product.model_validate({"category": "Woodwork"})
