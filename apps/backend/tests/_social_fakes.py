"""Shared test doubles for the Social Commerce suite."""

from __future__ import annotations


class FakeResponse:
    def __init__(self, status: int, json_data: dict | None = None,
                 text: str = ""):
        self.status_code = status
        self._json = json_data
        self.text = text

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> dict:
        if self._json is None:
            raise ValueError("no json body")
        return self._json


class FakeAsyncClient:
    """Drop-in for ``httpx.AsyncClient`` returning queued responses.

    ``calls`` records every request so tests can assert retry counts.
    """

    calls: list[tuple[str, str]] = []

    def __init__(self, queue: list[FakeResponse]):
        self._queue = queue

    def __call__(self, *args, **kwargs):  # AsyncClient(timeout=...)
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def request(self, method, url, data=None, params=None):
        FakeAsyncClient.calls.append((method, url))
        if len(self._queue) == 1:
            return self._queue[0]
        return self._queue.pop(0)


def patch_httpx(monkeypatch, responses: list[FakeResponse]) -> FakeAsyncClient:
    FakeAsyncClient.calls = []
    fake = FakeAsyncClient(responses)
    monkeypatch.setattr("httpx.AsyncClient", fake)
    return fake


def configure_meta(monkeypatch) -> None:
    """Give the cached Settings working Meta creds + zero backoff."""
    from app.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "meta_access_token", "tok", raising=False)
    monkeypatch.setattr(s, "facebook_page_id", "pg123", raising=False)
    monkeypatch.setattr(s, "social_retry_attempts", 3, raising=False)
    monkeypatch.setattr(s, "social_retry_backoff_s", (0, 0, 0),
                        raising=False)
