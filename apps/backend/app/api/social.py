"""Social Commerce REST surface.

Mirrors the MCP tools 1:1 and reuses the exact same service layer, so
there is one implementation behind two front doors (REST + MCP).
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter

from ..logging_conf import get_logger
from ..services.social.analytics_service import analytics_provider
from ..services.social.facebook_service import publish_facebook_post
from ..services.social.scheduler_service import scheduler_service
from ..services.social.social_generator import generate_social_content
from ..services.social.social_models import (
    FacebookPublishInput,
    FacebookPublishResult,
    Platform,
    ScheduleResult,
    SchedulePostInput,
    SocialContentBundle,
    SocialGenerationInput,
)
from ..services.social import account_store
import httpx
from ..config import get_settings

log = get_logger("hackai.social.api")
router = APIRouter(prefix="/api/social", tags=["social"])


@router.post("/generate", response_model=SocialContentBundle)
async def generate(data: SocialGenerationInput) -> SocialContentBundle:
    # Groq SDK is sync — keep the event loop free.
    return await asyncio.to_thread(generate_social_content, data)


@router.post("/facebook/publish", response_model=FacebookPublishResult)
async def facebook_publish(
    data: FacebookPublishInput,
    account_id: str | None = None,
) -> FacebookPublishResult:
    return await publish_facebook_post(data, account_id=account_id)


@router.post("/schedule", response_model=ScheduleResult)
async def schedule(data: SchedulePostInput) -> ScheduleResult:
    return scheduler_service.schedule(data)


# --- OAuth & account management (minimal demo endpoints) ----------------- #


@router.get("/auth/meta/oauth")
async def meta_oauth_url(platform: str | None = None) -> dict:
    """Return an OAuth redirect URL for Meta (app must be configured).

    The frontend should open this URL in a browser to complete the OAuth flow.
    """
    s = get_settings()
    if not s.meta_app_id or not s.meta_app_secret:
        return {"error": "Meta OAuth not configured on server"}
    redirect = s.meta_redirect_uri_resolved
    # Facebook-only for the MVP. Instagram scopes (instagram_basic,
    # instagram_content_publish) are intentionally dropped — adding scopes
    # the app hasn't been granted makes the whole OAuth dialog fail with
    # "Invalid Scopes".
    # business_management lets us discover Pages owned by a Business
    # Portfolio (New Pages Experience), which /me/accounts never returns.
    scope = (
        "pages_show_list,pages_manage_posts,"
        "pages_read_engagement,business_management"
    )
    url = (
        f"https://www.facebook.com/{s.meta_graph_version}/dialog/oauth"
        f"?client_id={s.meta_app_id}&redirect_uri={redirect}&scope={scope}&response_type=code"
    )
    return {"redirect_url": url}


@router.get("/auth/meta/callback")
async def meta_oauth_callback(code: str | None = None, platform: str | None = None) -> dict:
    """Exchange `code` for a short-lived token and list linked pages/accounts.

    This endpoint assumes the frontend will forward the `code` query param
    returned by Meta. For demo/testing we accept a direct `access_token`
    in place of `code` if present.
    """
    s = get_settings()
    if not s.meta_app_id or not s.meta_app_secret:
        return {"error": "Meta app not configured"}

    async with httpx.AsyncClient(timeout=10) as client:
        if not code:
            return {"error": "Missing code"}
        # Exchange code for access token
        redirect = s.meta_redirect_uri_resolved
        token_url = (
            f"https://graph.facebook.com/{s.meta_graph_version}/oauth/access_token"
            f"?client_id={s.meta_app_id}&redirect_uri={redirect}"
            f"&client_secret={s.meta_app_secret}&code={code}"
        )
        resp = await client.get(token_url)
        if resp.status_code != 200:
            return {"error": "Token exchange failed", "details": resp.text}
        user_token = resp.json().get("access_token")

        # Upgrade the short-lived user token to a long-lived one (~60 days).
        # Page tokens derived from a long-lived user token do not expire,
        # which is what we want for a stable FACEBOOK_PAGE_ID/token pair.
        ll_resp = await client.get(
            f"https://graph.facebook.com/{s.meta_graph_version}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": s.meta_app_id,
                "client_secret": s.meta_app_secret,
                "fb_exchange_token": user_token,
            },
        )
        if ll_resp.status_code == 200:
            user_token = ll_resp.json().get("access_token", user_token)

        # List pages the user manages — each entry carries its OWN Page
        # access token, which is what {page_id}/photos requires.
        pages_url = f"https://graph.facebook.com/{s.meta_graph_version}/me/accounts"
        pages_resp = await client.get(pages_url, params={"access_token": user_token})
        if pages_resp.status_code != 200:
            return {"error": "Failed to list pages", "details": pages_resp.text}
        pages = pages_resp.json().get("data", [])

        # /me/accounts only returns "classic" admin Pages. Pages owned by a
        # Business Portfolio (New Pages Experience) never appear there — find
        # them via /me/businesses → owned_pages/client_pages, then fetch a
        # real Page access token for each so publishing works.
        businesses_raw: dict = {}
        if not pages:
            biz_resp = await client.get(
                f"https://graph.facebook.com/{s.meta_graph_version}/me/businesses",
                params={"access_token": user_token, "fields": "id,name"},
            )
            businesses_raw = biz_resp.json()
            seen: set[str] = set()
            for biz in businesses_raw.get("data", []):
                bid = biz.get("id")
                for edge in ("owned_pages", "client_pages"):
                    bp = await client.get(
                        f"https://graph.facebook.com/{s.meta_graph_version}/{bid}/{edge}",
                        params={"access_token": user_token, "fields": "id,name"},
                    )
                    for pg in bp.json().get("data", []):
                        pid = pg.get("id")
                        if not pid or pid in seen:
                            continue
                        seen.add(pid)
                        # Mint a Page access token for this business-owned Page.
                        tok_resp = await client.get(
                            f"https://graph.facebook.com/{s.meta_graph_version}/{pid}",
                            params={"access_token": user_token, "fields": "access_token,name"},
                        )
                        tok = tok_resp.json().get("access_token")
                        pages.append({
                            "id": pid,
                            "name": pg.get("name") or tok_resp.json().get("name"),
                            "access_token": tok or user_token,
                        })

        # Still nothing → surface exactly what Meta granted/returned.
        if not pages:
            me_resp = await client.get(
                f"https://graph.facebook.com/{s.meta_graph_version}/me",
                params={"access_token": user_token, "fields": "id,name"},
            )
            perms_resp = await client.get(
                f"https://graph.facebook.com/{s.meta_graph_version}/me/permissions",
                params={"access_token": user_token},
            )
            granted = [
                p["permission"]
                for p in perms_resp.json().get("data", [])
                if p.get("status") == "granted"
            ]
            return {
                "ok": False,
                "linked": [],
                "env": None,
                "diagnostic": {
                    "reason": "Meta returned no Pages for this user.",
                    "likely_cause": (
                        "No Page is admin-linked to this account and none was "
                        "found in any Business Portfolio. Check the Page's "
                        "access settings / that you accepted the Page invite."
                    ),
                    "me": me_resp.json(),
                    "granted_permissions": granted,
                    "me_accounts_raw": pages_resp.json(),
                    "me_businesses_raw": businesses_raw,
                },
            }

        linked: list[dict] = []
        for p in pages:
            page_id = p.get("id")
            # The Page access token (NOT the user token) — required to
            # publish on behalf of the Page.
            page_token = p.get("access_token") or user_token
            entry = {
                "provider": "facebook",
                "id": str(page_id),
                "name": p.get("name"),
                "page_id": page_id,
                "access_token": page_token,
            }
            account_store.add_account(entry)
            linked.append(entry)

        # Ready-to-paste .env lines for the first linked Facebook Page,
        # so testing global publishing is copy/paste instead of guesswork.
        fb = next((e for e in linked if e["provider"] == "facebook"), None)
        env_hint = None
        if fb:
            env_hint = {
                "FACEBOOK_PAGE_ID": fb["page_id"],
                "META_ACCESS_TOKEN": fb["access_token"],
            }

        return {"ok": True, "linked": linked, "env": env_hint}


@router.get("/auth/meta/accounts")
async def meta_accounts() -> dict:
    return {"accounts": account_store.list_accounts()}


@router.post("/auth/meta/unlink")
async def meta_unlink(provider: str, account_id: str) -> dict:
    ok = account_store.unlink_account(provider, account_id)
    return {"ok": ok}


@router.get("/analytics")
async def campaign_analytics(platform: Platform, post_id: str) -> dict:
    # Interface only — raises AnalyticsNotImplementedError (501 envelope).
    return await analytics_provider.get_campaign_analytics(
        platform=platform, post_id=post_id
    )
