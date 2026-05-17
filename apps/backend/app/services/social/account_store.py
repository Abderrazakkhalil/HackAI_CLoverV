"""Tiny persistence for linked Meta accounts (development/demo use).

This stores linked pages/business accounts and tokens in a JSON file
under the app directory. It is intentionally minimal — intended for
development and demo. Tokens are stored as-is; for production use a
proper encrypted store is required.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...config import get_settings

_STORAGE: dict[str, Any] | None = None


def _path() -> Path:
    s = get_settings()
    return Path(s.graph_base_url or ".").parents[0] / "social_accounts.json"


def _load() -> dict[str, Any]:
    global _STORAGE
    if _STORAGE is not None:
        return _STORAGE
    p = Path(__file__).resolve().parents[2] / "social_accounts.json"
    if p.exists():
        try:
            _STORAGE = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            _STORAGE = {"accounts": []}
    else:
        _STORAGE = {"accounts": []}
    return _STORAGE


def _save() -> None:
    s = _load()
    p = Path(__file__).resolve().parents[2] / "social_accounts.json"
    p.write_text(json.dumps(s, indent=2), encoding="utf-8")


def add_account(entry: dict[str, Any]) -> None:
    s = _load()
    # dedupe by provider+id
    accounts = [a for a in s.get("accounts", []) if not (
        a.get("provider") == entry.get("provider") and a.get("id") == entry.get("id")
    )]
    accounts.append(entry)
    s["accounts"] = accounts
    _save()


def list_accounts() -> list[dict[str, Any]]:
    s = _load()
    return s.get("accounts", [])


def unlink_account(provider: str, account_id: str) -> bool:
    s = _load()
    accounts = [a for a in s.get("accounts", []) if not (
        a.get("provider") == provider and a.get("id") == account_id
    )]
    changed = len(accounts) != len(s.get("accounts", []))
    s["accounts"] = accounts
    _save()
    return changed


def find_account(provider: str, account_id: str) -> dict[str, Any] | None:
    """Return an account entry matching provider+id or page_id."""
    for a in list_accounts():
        if a.get("provider") == provider and a.get("id") == account_id:
            return a
        if a.get("page_id") == account_id:
            return a
    return None
