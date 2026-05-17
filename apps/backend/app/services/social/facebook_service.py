"""Facebook Page publishing via the real Meta Graph API.

Publishing rules (driven by what the artisan provided up front):
- An uploaded photo (``image_data_url``) → the bytes are uploaded to
  the Page as a real file (``/{page}/photos``).
- No image → a text-only Page post (``/{page}/feed``).
- ``image_url`` (a public URL, used by the scheduler) → photo by URL.
"""

from __future__ import annotations

import base64
import binascii

from ...config import get_settings
from ...logging_conf import get_logger
from .meta_client import graph_request, require_meta_credentials
from .social_exceptions import FacebookPublishError
from .social_models import FacebookPublishInput, FacebookPublishResult
from .account_store import find_account

log = get_logger("hackai.social.fb")

_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


def _decode_data_url(data_url: str) -> tuple[bytes, str]:
    """``data:image/jpeg;base64,XXXX`` → (raw bytes, mime type)."""
    if not data_url.startswith("data:") or ";base64," not in data_url:
        raise FacebookPublishError(
            details="image_data_url must be a base64 data URL."
        )
    header, b64 = data_url.split(";base64,", 1)
    mime = header[len("data:"):] or "image/jpeg"
    try:
        return base64.b64decode(b64, validate=True), mime
    except (binascii.Error, ValueError) as exc:
        raise FacebookPublishError(
            details=f"Could not decode image data: {exc}"
        ) from exc


async def publish_facebook_post(
    data: FacebookPublishInput,
    account_id: str | None = None,
) -> FacebookPublishResult:
    """Publish to the specified Facebook Page.

    If ``account_id`` matches a linked account in ``account_store`` its
    token/page are used; otherwise the global ``FACEBOOK_PAGE_ID`` /
    ``META_ACCESS_TOKEN`` are used (and credentials are enforced).
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
        require_meta_credentials(need_facebook=True)
        page_id = s.facebook_page_id
        access_token = access_token or s.meta_access_token

    if data.image_data_url:
        # The artisan's uploaded photo → upload the real file bytes.
        raw, mime = _decode_data_url(data.image_data_url)
        filename = f"upload.{_EXT.get(mime, 'jpg')}"
        body = await graph_request(
            "POST",
            f"{page_id}/photos",
            error_cls=FacebookPublishError,
            data={"caption": data.caption, "published": "true"},
            files={"source": (filename, raw, mime)},
            access_token=access_token,
        )
    elif data.image_url:
        # Public URL (scheduler path) → let Graph fetch it.
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
            # Back-compat for tests/mocks without the access_token kw.
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
    else:
        # No image → text-only Page post.
        body = await graph_request(
            "POST",
            f"{page_id}/feed",
            error_cls=FacebookPublishError,
            data={"message": data.caption},
            access_token=access_token,
        )

    post_id = body.get("post_id") or body.get("id")
    if not post_id:
        raise FacebookPublishError(
            details=f"No post id in response: {body}"
        )

    log.info("Facebook post published: %s", post_id)
    return FacebookPublishResult(post_id=str(post_id))
