"""Deterministic entitlement logic. LLM-free, unit-tested. Tier order FREE<PLUS<PREMIUM."""
from __future__ import annotations

TIER_ORDER = {"FREE": 0, "PLUS": 1, "PREMIUM": 2}


def can_play(user_id: str, min_package: str) -> dict:
    """Return {"can_play": bool, "user_tier": str, "min_tier_needed": str}."""
    raise NotImplementedError("Phase 3: load users.jsonl, compare tiers via TIER_ORDER")
