"""Hirafi extraction prompts (ported from the production pipeline).

Kept in one place so the FastAPI orchestrator and the MCP prompt expose
exactly the same instruction to the model.
"""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are a multilingual e-commerce product data extraction expert specializing in \
Moroccan handmade goods. You receive a raw Darija (Moroccan Arabic) transcript \
describing a handmade product dictated by a Moroccan artisan.

Your task:
1. Understand the Darija transcript fully.
2. Extract every possible product attribute.
3. Translate descriptions into English, French, and Modern Standard Arabic.
4. Return a SINGLE valid JSON object — no markdown fences, no extra text.

Rules:
- Fill every field. Use null ONLY if truly impossible to infer.
- Titles must be SEO-optimized, max 80 characters.
- English descriptions should be 3-5 sentences highlighting craftsmanship, origin, and use case.
- Tags should be English SEO keywords (8-15 tags).
- Price currency defaults to "MAD". Convert to USD estimate using rate 0.099.
- **Price extraction rule (CRITICAL):** Set `price_mentioned` to `true` ONLY
  if the artisan said an actual number AND a currency word (درهم / درهم /
  dirham / MAD / euro / dollar / دولار). Set it to `false` for everything
  else. When `price_mentioned` is `false`, ALWAYS set price.amount = 0 and
  price.price_usd_estimate = 0. Never guess or estimate a price.
- Country of origin is always "Morocco".
- confidence_score: your self-assessed confidence (0.0-1.0) in the extraction quality.
- missing_fields: list field names you could NOT fill with a brief reason each.
- Output ONLY the JSON object. No prose, no code fences, no explanation.\
"""

STRICT_RETRY_SUFFIX = """

CRITICAL: Your previous response was NOT valid JSON. This time you MUST return
ONLY a raw JSON object. No markdown code fences (```), no explanatory text before
or after, no trailing commas. Start with {{ and end with }}. Nothing else."""


def build_user_prompt(transcript: str) -> str:
    return f"""\
Here is the raw Darija transcript from a Moroccan artisan describing their product:

---
{transcript}
---

Extract all product information and return a JSON object with this EXACT structure:

{{
  "product": {{
    "title": {{
      "en": "short SEO-optimized English title (max 80 chars)",
      "fr": "French title",
      "ar": "Modern Standard Arabic title"
    }},
    "description": {{
      "en": "full marketing description in English (3-5 sentences)",
      "fr": "French description",
      "ar": "Arabic description"
    }},
    "category": "e.g. Rugs & Carpets, Pottery, Leather Goods, Jewelry, Textiles",
    "subcategory": "string or null",
    "tags": ["SEO", "keywords", "in", "English"],
    "price": {{
      "amount": 0,
      "currency": "MAD",
      "price_usd_estimate": 0.0,
      "negotiable": true
    }},
    "dimensions": {{
      "length_cm": null,
      "width_cm": null,
      "height_cm": null,
      "weight_kg": null
    }},
    "materials": ["list of materials in English"],
    "colors": ["list of colors"],
    "origin": {{
      "country": "Morocco",
      "region": "string or null",
      "technique": "string or null"
    }},
    "condition": "new | handmade-new | vintage",
    "quantity_available": null,
    "lead_time_days": null,
    "shipping": {{
      "local_available": true,
      "international_available": false,
      "fragile": false
    }},
    "artisan_notes": "any personal story the artisan shared, translated to English, or null",
    "raw_transcript": "{transcript}",
    "confidence_score": 0.0,
    "missing_fields": [],
    "price_mentioned": false
  }}
}}

Return ONLY valid JSON. No markdown, no code fences, no extra text."""
