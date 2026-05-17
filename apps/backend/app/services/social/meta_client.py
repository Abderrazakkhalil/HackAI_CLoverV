"""Shared Meta Graph API client.

One place for: credential checks, the request/parse logic, and the
retry policy (3 attempts, exponential 1s/2s/4s backoff, **never** retry
401/403). The Facebook service builds on this so the network
behaviour is consistent and not duplicated.
"""

from __future__ import annotations

import asyncio

import httpx

from ...config import get_settings
from ...logging_conf import get_logger
from .social_exceptions import SocialAuthError, SocialConfigError, SocialError

log = get_logger("hackai.social.meta")

_AUTH_STATUSES = {401, 403}


def require_meta_credentials(*, need_facebook: bool = False) -> None:
    """Fail fast (non-retryable) when required env vars are absent."""
    s = get_settings()
    missing: list[str] = []
    if not s.meta_access_token:
        missing.append("META_ACCESS_TOKEN")
    if need_facebook and not s.facebook_page_id:
        missing.append("FACEBOOK_PAGE_ID")
    if missing:
        raise SocialConfigError(
            "Social publishing is not configured.",
            details=f"Missing environment variables: {', '.join(missing)}",
        )


def _parse_graph_error(resp: httpx.Response) -> str:
    try:
        body = resp.json()
        err = body.get("error", {})
        return (
            f"HTTP {resp.status_code} | "
            f"type={err.get('type')} code={err.get('code')} "
            f"subcode={err.get('error_subcode')} "
            f"message={err.get('message')}"
        )
    except (ValueError, AttributeError):
        return f"HTTP {resp.status_code} | {resp.text[:300]}"


async def graph_request(
    method: str,
    path: str,
    *,
    error_cls: type[SocialError],
    data: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
    files: dict[str, tuple] | None = None,
    access_token: str | None = None,
) -> dict:
    """Execute one Graph call with the project retry policy.

    Returns the parsed JSON body. Raises :class:`SocialAuthError`
    immediately on 401/403; raises ``error_cls`` after retries are
    exhausted for transient failures.
    """
    s = get_settings()
    url = f"{s.graph_base_url}/{path.lstrip('/')}"
    backoff = s.social_retry_backoff_s
    attempts = max(1, s.social_retry_attempts)

    token = access_token or s.meta_access_token
    auth = {"access_token": token} if token else {}
    send_data = {**(data or {}), **auth} if method.upper() == "POST" else None
    send_params = {**(params or {}), **auth} if method.upper() == "GET" else None

    last_details = ""
    for attempt in range(attempts):
        try:
            async with httpx.AsyncClient(timeout=s.meta_api_timeout_s) as client:
                resp = await client.request(
                    method, url, data=send_data, params=send_params,
                    files=files if method.upper() == "POST" else None,
                )
        except httpx.RequestError as exc:
            last_details = f"network error: {exc!r}"
            log.warning("Graph %s %s failed (attempt %d): %s",
                        method, path, attempt + 1, last_details)
        else:
            if resp.status_code in _AUTH_STATUSES:
                # Never retry auth/permission failures.
                raise SocialAuthError(details=_parse_graph_error(resp))
            if resp.is_success:
                try:
                    return resp.json()
                except ValueError as exc:
                    raise error_cls(
                        details=f"Malformed Graph response: {exc}"
                    ) from exc
            last_details = _parse_graph_error(resp)
            # 4xx (non-auth) is a client error → not worth retrying.
            if 400 <= resp.status_code < 500 and resp.status_code != 429:
                raise error_cls(details=last_details)
            log.warning("Graph %s %s transient (attempt %d): %s",
                        method, path, attempt + 1, last_details)

        if attempt < attempts - 1:
            delay = backoff[min(attempt, len(backoff) - 1)]
            await asyncio.sleep(delay)

    raise error_cls(
        details=f"Exhausted {attempts} attempts. Last error: {last_details}"
    )
