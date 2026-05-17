"""FastAPI dependencies.

``get_current_user`` validates the caller's Supabase JWT and returns the
matching profile (creating a minimal one on first use).
"""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

from .schemas_db import AuthUser
from .supabase_client import get_supabase


async def get_current_user(
    authorization: str | None = Header(default=None),
) -> AuthUser:
    """Verify ``Authorization: Bearer <jwt>`` and load the profile."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header.",
        )
    token = authorization.split(" ", 1)[1].strip()
    sb = get_supabase()

    try:
        result = sb.auth.get_user(token)
    except Exception as exc:  # noqa: BLE001 - network / token errors
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
        ) from exc

    user = getattr(result, "user", None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token did not resolve to a user.",
        )

    # Load (or lazily create) the profile row.
    profile_resp = (
        sb.table("profiles").select("*").eq("id", user.id).limit(1).execute()
    )
    rows = profile_resp.data or []
    if rows:
        p = rows[0]
        return AuthUser(
            id=user.id,
            email=user.email,
            full_name=p.get("full_name", ""),
            city_region=p.get("city_region", ""),
            phone=p.get("phone", ""),
        )

    sb.table("profiles").insert({"id": user.id}).execute()
    return AuthUser(id=user.id, email=user.email)


CurrentUser = Depends(get_current_user)
