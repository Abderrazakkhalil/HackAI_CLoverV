"""Centralized, validated configuration.

All runtime knobs live here so the rest of the codebase never reads
``os.environ`` directly. Values are loaded from the repo-root ``.env``
(so the whole team shares one secrets file) with sane demo-safe defaults.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root = three levels up from this file (app/ -> backend/ -> apps/ -> root)
REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", REPO_ROOT / "apps" / "backend" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Server ---
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_origin: str = "http://localhost:3000"
    log_level: str = "INFO"

    # --- Speech-to-Text: MoulSot Gradio Space ---
    hf_token: str = ""
    asr_space: str = "atlasia/MoulSot.v0.3"
    asr_lang: str = "Auto (Darija / Arabic)"
    asr_timeout_s: float = 90.0

    # --- LLM: Groq (primary + fallback model) ---
    groq_api_key: str = ""
    groq_primary_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    groq_fallback_model: str = "llama-3.3-70b-versatile"

    # --- Social Commerce: Meta Graph API ---
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_redirect_uri: str = ""
    meta_access_token: str = ""
    facebook_page_id: str = ""
    meta_graph_version: str = "v21.0"
    meta_api_timeout_s: float = 30.0

    # --- Social: external-call retry policy ---
    social_retry_attempts: int = 3
    social_retry_backoff_s: tuple[float, float, float] = (1.0, 2.0, 4.0)

    # --- Social: scheduler persistence ---
    social_db_path: str = str(
        Path(__file__).resolve().parents[1] / "social_schedule.db"
    )

    # --- Limits ---
    max_audio_bytes: int = 15 * 1024 * 1024  # 15 MB
    max_image_bytes: int = 10 * 1024 * 1024  # 10 MB
    llm_max_retries: int = 1

    # --- Pipeline identity (surfaced in response meta) ---
    pipeline_version: str = "4.0.0"

    @property
    def graph_base_url(self) -> str:
        return f"https://graph.facebook.com/{self.meta_graph_version}"

    @property
    def meta_redirect_uri_resolved(self) -> str:
        """OAuth redirect: explicit ``META_REDIRECT_URI`` wins, else derive
        it from the frontend origin (back-compat default)."""
        return (
            self.meta_redirect_uri
            or f"{self.frontend_origin}/api/social/auth/meta/callback"
        )

    @property
    def allowed_audio_types(self) -> set[str]:
        return {
            "audio/wav",
            "audio/x-wav",
            "audio/mpeg",
            "audio/mp3",
            "audio/webm",
            "audio/ogg",
            "audio/mp4",
            "audio/x-m4a",
        }

    @property
    def allowed_image_types(self) -> set[str]:
        return {"image/jpeg", "image/png", "image/webp"}


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor (import-safe, instantiated once)."""
    return Settings()
