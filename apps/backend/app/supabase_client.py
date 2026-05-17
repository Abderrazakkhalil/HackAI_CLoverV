"""Singleton Supabase client (service-role).

Use this for all server-side DB / Auth operations. The service-role key
bypasses RLS — never expose it to the browser.
"""

from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from .config import get_settings
from .errors import HackAIError


class SupabaseConfigError(HackAIError):
    status_code = 500
    message = "Supabase is not configured."


@lru_cache
def get_supabase() -> Client:
    """Return a cached service-role Supabase client."""
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        raise SupabaseConfigError(
            detail="Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env.",
        )
    return create_client(settings.supabase_url, settings.supabase_service_key)
