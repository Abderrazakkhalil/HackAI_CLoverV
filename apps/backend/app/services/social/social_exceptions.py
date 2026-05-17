"""Explicit Social Commerce errors.

Every failure is one of these — nothing fails silently. They carry a
machine ``code``, a safe ``message`` and a ``details`` string, and render
to the required envelope::

    {"error": {"code": "", "message": "", "details": ""}}
"""

from __future__ import annotations


class SocialError(Exception):
    """Base. ``retryable`` gates the external-call retry policy."""

    code = "social_error"
    message = "Social commerce operation failed."
    status_code = 502
    retryable = True

    def __init__(self, message: str | None = None, details: str = ""):
        self.message = message or self.message
        self.details = details
        super().__init__(self.message)

    def to_envelope(self) -> dict:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class SocialConfigError(SocialError):
    code = "social_not_configured"
    message = "Social commerce is not configured."
    status_code = 503
    retryable = False


class SocialAuthError(SocialError):
    """Meta returned 401/403 — never retried."""

    code = "social_auth_error"
    message = "Meta Graph API authentication or permission failed."
    status_code = 401
    retryable = False


class SocialGenerationError(SocialError):
    code = "social_generation_error"
    message = "Could not generate social media content."
    status_code = 502
    retryable = False


class FacebookPublishError(SocialError):
    code = "facebook_publish_error"
    message = "Could not publish the Facebook post."
    status_code = 502


class SchedulingError(SocialError):
    code = "scheduling_error"
    message = "Could not schedule the post."
    status_code = 500
    retryable = False


class AnalyticsNotImplementedError(SocialError):
    code = "analytics_not_implemented"
    message = "Campaign analytics is not implemented yet."
    status_code = 501
    retryable = False
