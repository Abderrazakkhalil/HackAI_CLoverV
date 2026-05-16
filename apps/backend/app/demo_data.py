"""Seeded artisan products for DEMO_MODE and as MCP resources.

These guarantee a flawless live demo even with zero internet, and match
the rich Hirafi pipeline schema.
"""

from __future__ import annotations

from .schemas import (
    Dimensions,
    LocalizedText,
    Origin,
    Price,
    Product,
    Shipping,
)

DEMO_TRANSCRIPT = (
    "هاد الزربية دمغة من عندي، طولها متران، بمية وخمسين درهم، "
    "صنعة يدوية من الصوف الطبيعي، كنبيع محليا وخارج البلاد"
)

DEMO_PRODUCTS: dict[str, Product] = {
    "berber-rug": Product(
        title=LocalizedText(
            en="Handwoven Atlas Berber Wool Rug — 2m Natural Wool",
            fr="Tapis Berbère de l'Atlas Tissé Main — Laine Naturelle 2m",
            ar="زربية أطلسية مصنوعة يدويًا من الصوف الطبيعي - مترين",
        ),
        description=LocalizedText(
            en=(
                "A one-of-a-kind Berber rug, hand-knotted by a single artisan "
                "from 100% natural sheep wool. Measuring two meters, it brings "
                "the warmth and heritage of the Atlas Mountains into any space. "
                "Each motif is dictated by tradition and the maker's own hand, "
                "so no two pieces are ever alike. Ships locally and worldwide."
            ),
            fr=(
                "Un tapis berbère unique, noué à la main en laine de mouton "
                "100% naturelle. Deux mètres de chaleur et d'héritage de "
                "l'Atlas pour sublimer votre intérieur."
            ),
            ar=(
                "زربية أمازيغية فريدة، منسوجة يدويًا من صوف الغنم الطبيعي "
                "بطول مترين، تضفي دفء وأصالة جبال الأطلس على أي مكان."
            ),
        ),
        category="Rugs & Carpets",
        subcategory="Berber Rug",
        tags=[
            "berber rug",
            "moroccan rug",
            "handwoven wool rug",
            "atlas mountains",
            "natural wool",
            "boho home decor",
            "artisan made",
            "handmade carpet",
        ],
        price=Price(
            amount=150,
            currency="MAD",
            price_usd_estimate=round(150 * 0.099, 2),
            negotiable=True,
        ),
        dimensions=Dimensions(length_cm=200, width_cm=120, weight_kg=4.5),
        materials=["natural sheep wool"],
        colors=["crimson", "honey", "ivory"],
        origin=Origin(
            country="Morocco",
            region="Atlas Mountains",
            technique="hand-knotting",
        ),
        condition="handmade-new",
        quantity_available=1,
        lead_time_days=7,
        shipping=Shipping(
            local_available=True,
            international_available=True,
            fragile=False,
        ),
        artisan_notes=(
            "The artisan stamps each rug with their own signature motif and "
            "sells both locally and abroad."
        ),
        raw_transcript=DEMO_TRANSCRIPT,
        confidence_score=0.92,
        missing_fields=[],
    ),
}

DEFAULT_DEMO_KEY = "berber-rug"
