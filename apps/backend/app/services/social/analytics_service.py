"""Campaign analytics — interface only (future extension).

Intentionally unimplemented: it raises rather than returning fabricated
numbers, consistent with the project's no-silent-failure philosophy.
When real Meta Insights integration lands, implement this method only;
callers and schemas stay unchanged.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .social_exceptions import AnalyticsNotImplementedError
from .social_models import Platform


class AnalyticsProvider(ABC):
    """Contract for a future analytics backend (e.g. Meta Insights)."""

    @abstractmethod
    async def get_campaign_analytics(
        self, *, platform: Platform, post_id: str
    ) -> dict:
        """Return engagement metrics for a published post."""
        raise NotImplementedError


class MetaInsightsProvider(AnalyticsProvider):
    async def get_campaign_analytics(
        self, *, platform: Platform, post_id: str
    ) -> dict:
        raise AnalyticsNotImplementedError(
            details=(
                "Meta Insights integration is planned. "
                f"Requested platform={platform} post_id={post_id}."
            )
        )


analytics_provider: AnalyticsProvider = MetaInsightsProvider()
