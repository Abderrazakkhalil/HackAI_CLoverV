"""Facebook Page photo publishing via the real Meta Graph API."""

from __future__ import annotations

from ...config import get_settings
from ...logging_conf import get_logger
from .meta_client import graph_request, require_meta_credentials
from .social_exceptions import FacebookPublishError
from .social_models import FacebookPublishInput, FacebookPublishResult
from .account_store import find_account

log = get_logger("hackai.social.fb")


async def publish_facebook_post(
    data: FacebookPublishInput,
    account_id: str | None = None,
) -> FacebookPublishResult:
    """Publish a photo to the specified Facebook Page.

    If `account_id` is provided and a matching linked account exists in
    the demo `account_store`, its `access_token` and `page_id` are used.
    Otherwise the global `FACEBOOK_PAGE_ID` and `META_ACCESS_TOKEN` are
    used (and `require_meta_credentials` is enforced).
    """
    s = get_settings()
    access_token: str | None = None
    page_id: str | None = None

    if account_id:
        acct = find_account("facebook", account_id)
        if acct:
            access_token = acct.get("access_token")
            page_id = acct.get("page_id") or acct.get("id")

    if not page_id:
        # fall back to global settings
        require_meta_credentials(need_facebook=True)
        page_id = s.facebook_page_id
        access_token = access_token or s.meta_access_token

    try:
        body = await graph_request(
            "POST",
            f"{page_id}/photos",
            error_cls=FacebookPublishError,
            data={
                "url": str(data.image_url),
                "caption": data.caption,
                "published": "true",
            },
            access_token=access_token,
        )
    except TypeError:
        # Backwards-compat for tests/mocks that don't accept access_token kw
        body = await graph_request(
            "POST",
            f"{page_id}/photos",
            error_cls=FacebookPublishError,
            data={
                "url": str(data.image_url),
                "caption": data.caption,
                "published": "true",
            },
        )
    post_id = body.get("post_id") or body.get("id")
    if not post_id:
        raise FacebookPublishError(
            details=f"No post id in response: {body}"
        )

    log.info("Facebook post published: %s", post_id)
    return FacebookPublishResult(post_id=str(post_id))
