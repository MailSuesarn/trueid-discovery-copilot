"""Governance layer: decide the policy-approved action + whether an upsell/offer is eligible.

Enforces monetization.max_discount_pct and min_tier IN CODE (never trusts the LLM). This is
what makes `action` a deterministic, exact-match eval target. See ARCHITECTURE.md §5.
"""
from __future__ import annotations


def find_privileges(user_id: str, query: str | None = None) -> list[dict]:
    """Return privileges the user is eligible for (gated by min_tier)."""
    raise NotImplementedError("Phase 3")


def decide_action(user_id: str, intent: str, context: dict) -> dict:
    """The policy. Return {"action": "play|upgrade|redeem|none",
    "upsell": {"package": str|None, "reason_th": str|None}} respecting the discount ceiling."""
    raise NotImplementedError("Phase 3")
