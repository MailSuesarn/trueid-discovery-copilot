"""Deterministic entitlement logic. LLM-free, unit-tested. Tier order FREE<PLUS<PREMIUM."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

TIER_ORDER = {"FREE": 0, "PLUS": 1, "PREMIUM": 2}
DATA_DIR = Path("data")


@lru_cache
def _load_users() -> dict:
    path = DATA_DIR / "users.jsonl"
    if not path.exists():
        return {}
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {r["user_id"]: r for r in rows}


def get_user(user_id: str) -> dict | None:
    return _load_users().get(user_id)


def user_tier(user_id: str) -> str:
    user = get_user(user_id)
    return user["tier"] if user else "FREE"


def can_play(user_id: str, min_package: str) -> dict:
    """Return {"can_play": bool, "user_tier": str, "min_tier_needed": str}."""
    tier = user_tier(user_id)
    can = TIER_ORDER.get(tier, 0) >= TIER_ORDER.get(min_package, 99)
    return {"can_play": can, "user_tier": tier, "min_tier_needed": min_package}
