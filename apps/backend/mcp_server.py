"""Hirfati MCP server.

Why MCP here
------------
The Hirafi pipeline is a small set of well-defined capabilities:
transcribe Darija audio, and turn a description into a rich, validated
multilingual product listing. Exposing them over MCP means *any*
MCP-aware agent (Claude Desktop, an IDE, an orchestrator) can drive the
artisan workflow with typed inputs and structured outputs — the exact
same code the web app uses, no REST glue required.

- Tools   = the artisan pipeline + the Social Commerce tools.
- Prompts = the reusable extraction prompt.

Run: ``python mcp_server.py``  (stdio transport)
"""

from __future__ import annotations

import asyncio
import base64

from mcp.server.fastmcp import FastMCP

from app.logging_conf import configure_logging, get_logger
from app.prompts import SYSTEM_PROMPT, build_user_prompt
from app.schemas import Artisan
from app.services.llm import generate_product
from app.services.orchestrator import run_pipeline
from app.services.transcription import transcribe
from mcp_social_tools import register as register_social_tools

configure_logging("INFO")
log = get_logger("hackai.mcp")

mcp = FastMCP("hirfati")

# Social Commerce tools (generate / publish / schedule / analytics).
register_social_tools(mcp)


# --------------------------------------------------------------------------- #
# Tools
# --------------------------------------------------------------------------- #
@mcp.tool()
async def transcribe_audio(audio_base64: str, filename: str = "audio.webm") -> dict:
    """Transcribe a base64-encoded Darija audio clip via MoulSot.

    Returns ``{text, language, source, inference_ms}``. Falls back to a
    mock transcription if MoulSot is unavailable so the call never fails.
    """
    audio_bytes = base64.b64decode(audio_base64)
    result, inference_ms = await asyncio.to_thread(
        transcribe, audio_bytes, filename, None
    )
    return {**result.model_dump(), "inference_ms": inference_ms}


@mcp.tool()
async def generate_product_listing(transcription: str) -> dict:
    """Turn a Darija transcription into a schema-validated rich listing.

    Output strictly matches the multilingual Product schema (titles,
    descriptions, price, dimensions, materials, origin, ...).
    """
    product, label = await asyncio.to_thread(generate_product, transcription)
    return {"product": product.model_dump(), "llm_model": label}


@mcp.tool()
async def process_artisan_product(
    audio_base64: str,
    filename: str = "audio.webm",
    image_base64: str | None = None,
    image_filename: str | None = None,
    artisan_full_name: str | None = None,
    artisan_city_region: str | None = None,
    artisan_phone: str | None = None,
) -> dict:
    """Full pipeline: audio (+ optional image, + artisan) -> JSON + meta."""
    audio_bytes = base64.b64decode(audio_base64)
    image_bytes = base64.b64decode(image_base64) if image_base64 else None
    artisan = None
    if artisan_full_name or artisan_city_region or artisan_phone:
        artisan = Artisan(
            full_name=artisan_full_name or "",
            city_region=artisan_city_region or "",
            phone=artisan_phone or "",
        )
    response = await run_pipeline(
        audio_bytes=audio_bytes,
        audio_filename=filename,
        audio_content_type=None,
        image_bytes=image_bytes,
        image_filename=image_filename,
        image_content_type="image/jpeg",
        artisan=artisan,
    )
    return response.model_dump()


# --------------------------------------------------------------------------- #
# Prompts
# --------------------------------------------------------------------------- #
@mcp.prompt()
def artisan_copywriter(transcription: str) -> str:
    """Reusable extraction prompt: Darija description -> listing JSON."""
    return SYSTEM_PROMPT + "\n\n---\n\n" + build_user_prompt(transcription)


async def _main() -> None:
    # Start the scheduler in this process so schedule_post executes here
    # too (pending jobs are reloaded from SQLite).
    from app.services.social.scheduler_service import scheduler_service

    scheduler_service.start()
    try:
        await mcp.run_stdio_async()
    finally:
        scheduler_service.shutdown()


if __name__ == "__main__":
    log.info("Starting Hirfati MCP server (stdio)…")
    asyncio.run(_main())
