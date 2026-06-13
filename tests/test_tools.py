"""Deterministic tools: entitlement tier logic + privilege policy ceiling."""
from __future__ import annotations

from app.core.config import get_settings
from app.tools.entitlement import TIER_ORDER, can_play
from app.tools.privilege import decide_action, find_privileges


def test_tier_ordering_constants():
    assert TIER_ORDER["FREE"] < TIER_ORDER["PLUS"] < TIER_ORDER["PREMIUM"]


def test_can_play_respects_tier_floor():
    assert can_play("u_003", "PREMIUM")["can_play"] is True   # PREMIUM user
    assert can_play("u_001", "PLUS")["can_play"] is True      # PLUS user, PLUS item
    assert can_play("u_001", "PREMIUM")["can_play"] is False  # PLUS user, PREMIUM item
    assert can_play("u_002", "PLUS")["can_play"] is False     # FREE user, PLUS item


def test_policy_play_when_user_tier_meets_target():
    out = decide_action("u_003", "live_schedule", {"target_min_package": "PREMIUM"})
    assert out["action"] == "play"
    assert out["upsell"]["package"] is None


def test_policy_upgrade_when_user_tier_below_target():
    out = decide_action("u_001", "live_schedule", {"target_min_package": "PREMIUM"})
    assert out["action"] == "upgrade"
    assert out["upsell"]["package"] == "TrueID Premium"


def test_policy_redeem_when_privileges_eligible():
    privs = find_privileges("u_002", "กาแฟ")
    out = decide_action("u_002", "find_privilege", {"privileges": privs})
    assert out["action"] == "redeem"


def test_policy_recommends_premium_upgrade_for_free_user():
    out = decide_action("u_002", "recommend_package", {})
    assert out["action"] == "upgrade"
    assert out["upsell"]["package"] == "TrueID Premium"


def test_policy_no_offer_when_already_premium_recommendation():
    out = decide_action("u_003", "recommend_package", {})
    assert out["action"] == "none"


def test_discount_ceiling_enforced_by_policy():
    """Any privilege whose discount exceeds the configured ceiling must be dropped."""
    ceiling = get_settings().monetization.max_discount_pct
    rogue = [{
        "id": "p-999", "partner": "Test", "title_th": "rogue offer",
        "category": "shopping", "cost_points": 0,
        "discount_pct": ceiling + 50, "min_tier": "FREE",
    }]
    out = decide_action("u_002", "find_privilege", {"privileges": rogue})
    assert out["action"] == "none"
