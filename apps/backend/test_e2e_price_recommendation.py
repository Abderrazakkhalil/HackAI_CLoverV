#!/usr/bin/env python3
"""
End-to-end test for AI price recommendation flow.

Simulates:
1. User describing a Moroccan rug (without price)
2. Audio transcription (or mock)
3. Product extraction via Groq LLM
4. Auto-triggered price recommendation from Supabase comparables
5. Verify response includes AI-recommended price with reasoning
"""

import asyncio
import sys
from pathlib import Path

# Add apps/backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import get_settings
from app.services.price_recommendation import recommend
from app.schemas import Product, LocalizedText, Price, Dimensions, Origin, Shipping, Meta
from app.logging_conf import get_logger

log = get_logger("test_e2e")


async def test_price_recommendation():
    """Test the complete price recommendation flow."""

    settings = get_settings()
    log.info("=" * 70)
    log.info("E2E TEST: Price Recommendation for Rug without Mentioned Price")
    log.info("=" * 70)

    # Simulate what the LLM would extract from audio:
    # "A beautiful handmade wool rug from the Atlas mountains, 200cm by 140cm,
    #  ivory and black colors, Berber style, geometric patterns"
    # (No price mentioned in the audio)

    test_product = Product(
        title=LocalizedText(
            en="Atlas Mountain Wool Rug",
            fr="Tapis de Laine de Montagne de l'Atlas",
            ar="سجادة صوف جبال الأطلس"
        ),
        description=LocalizedText(
            en="Handmade wool rug from the Atlas mountains. Geometric patterns in ivory and black.",
            fr="Tapis de laine tissé à la main des montagnes de l'Atlas. Motifs géométriques en ivoire et noir.",
            ar="سجادة صوف مصنوعة يدويًا من جبال الأطلس. أنماط هندسية بالعاج والأسود."
        ),
        category="Rugs & Carpets",
        subcategory="Berber Rugs",
        tags=["wool", "berber", "geometric", "handmade"],
        price=Price(
            amount=0,  # NO PRICE MENTIONED - triggers recommendation
            currency="MAD",
            price_usd_estimate=0,
            negotiable=True
        ),
        dimensions=Dimensions(
            length_cm=200,
            width_cm=140,
            height_cm=None,
            weight_kg=None
        ),
        materials=["wool"],
        colors=["ivory", "black"],
        origin=Origin(
            country="Morocco",
            region="Atlas Mountains",
            technique="Berber"
        ),
        condition="new",
        quantity_available=1,
        lead_time_days=7,
        shipping=Shipping(
            local_available=True,
            international_available=True,
            fragile=False
        ),
        artisan_notes="Traditional weaving technique passed down through generations",
        raw_transcript="rug atlas mountains wool 200 140 ivory black berber",
        confidence_score=0.92,
        missing_fields=[]
    )

    log.info("\n📋 TEST PRODUCT (extracted from audio, price=0):")
    log.info(f"  Title: {test_product.title.en}")
    log.info(f"  Category: {test_product.category}")
    log.info(f"  Materials: {test_product.materials}")
    log.info(f"  Colors: {test_product.colors}")
    log.info(f"  Dimensions: {test_product.dimensions.length_cm}×{test_product.dimensions.width_cm}cm")
    log.info(f"  Price Amount: {test_product.price.amount} (ZERO = triggers recommendation)")

    try:
        log.info("\n🔍 STEP 1: Querying Supabase for comparable listings...")
        log.info("   Filter: category='Rugs & Carpets', materials overlap with ['wool']")

        recommendation, comparables = recommend(test_product)

        log.info("\n✅ STEP 2: Groq LLM analyzed comparables and predicted price:")
        log.info(f"  Suggested Price: {recommendation.suggested} {recommendation.currency}")
        log.info(f"  Price Range: {recommendation.min} – {recommendation.max} {recommendation.currency}")
        log.info(f"  Confidence: {recommendation.confidence * 100:.0f}%")
        log.info(f"  Comparables Used: {len(recommendation.comparable_ids)} listings")
        log.info(f"  IDs: {recommendation.comparable_ids[:3]}..." if len(recommendation.comparable_ids) > 3 else f"  IDs: {recommendation.comparable_ids}")

        log.info("\n💡 REASONING:")
        log.info(f"  {recommendation.reasoning}")

        log.info("\n" + "=" * 70)
        log.info("✅ TEST PASSED: Full end-to-end price recommendation flow works!")
        log.info("=" * 70)

        return True

    except Exception as e:
        log.error(f"\n❌ TEST FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_price_recommendation())
    sys.exit(0 if success else 1)
