"""Email + password auth backed by Supabase Auth (gotrue).

The service-role client lets us create users without an email
confirmation round-trip; for production you would disable
``email_confirm=True`` and let users verify via Supabase's built-in flow.
"""

from __future__ import annotations

from ..errors import HackAIError
from ..logging_conf import get_logger
from ..schemas_db import AuthResponse, AuthUser, LoginRequest, SignupRequest
from ..supabase_client import get_supabase

log = get_logger("hackai.auth")


class AuthError(HackAIError):
    status_code = 401
    message = "Authentication failed."


def _upsert_profile(user_id: str, payload: SignupRequest) -> None:
    sb = get_supabase()
    sb.table("profiles").upsert(
        {
            "id": user_id,
            "full_name": payload.full_name,
            "city_region": payload.city_region,
            "phone": payload.phone,
        }
    ).execute()


def signup(payload: SignupRequest) -> AuthResponse:
    sb = get_supabase()
    try:
        result = sb.auth.admin.create_user(
            {
                "email": payload.email,
                "password": payload.password,
                "email_confirm": True,
            }
        )
    except Exception as exc:  # noqa: BLE001
        log.error("Signup failed for %s: %s", payload.email, exc)
        raise AuthError("Could not create account.", detail=str(exc)) from exc

    user = getattr(result, "user", None)
    if user is None:
        raise AuthError("Account creation returned no user.")

    _upsert_profile(user.id, payload)

    # Issue a session by signing in with the same credentials.
    return login(LoginRequest(email=payload.email, password=payload.password))


def login(payload: LoginRequest) -> AuthResponse:
    sb = get_supabase()
    try:
        result = sb.auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("Login failed for %s: %s", payload.email, exc)
        raise AuthError("Invalid email or password.", detail=str(exc)) from exc

    session = getattr(result, "session", None)
    user = getattr(result, "user", None)
    if session is None or user is None:
        raise AuthError("Login returned no session.")

    # Load profile (created on signup; falls back to defaults).
    p_resp = (
        sb.table("profiles").select("*").eq("id", user.id).limit(1).execute()
    )
    p = (p_resp.data or [{}])[0]

    return AuthResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        expires_in=session.expires_in,
        user=AuthUser(
            id=user.id,
            email=user.email,
            full_name=p.get("full_name", ""),
            city_region=p.get("city_region", ""),
            phone=p.get("phone", ""),
        ),
    )
