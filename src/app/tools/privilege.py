"""Governance layer: decide the policy-approved action + whether an upsell/offer is eligible.

Enforces monetization.max_discount_pct and min_tier IN CODE (never trusts the LLM). This
is what makes `action` a deterministic, exact-match eval target. See ARCHITECTURE.md §5.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.tools.entitlement import TIER_ORDER, user_tier

DATA_DIR = Path("data")


@lru_cache
def _load_privileges() -> list[dict]:
    path = DATA_DIR / "privileges.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@lru_cache
def _load_packages() -> dict:
    path = DATA_DIR / "packages.json"
    if not path.exists():
        return {"packages": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _package_name_for_tier(tier: str) -> str | None:
    for pkg in _load_packages().get("packages", []):
        if pkg.get("tier") == tier:
            return pkg.get("name")
    return None


def find_privileges(user_id: str, query: str | None = None) -> list[dict]:
    """Return privileges the user is currently eligible for (tier gate + optional keyword filter)."""
    tier = user_tier(user_id)
    eligible = [
        p for p in _load_privileges()
        if TIER_ORDER.get(tier, 0) >= TIER_ORDER.get(p.get("min_tier", "FREE"), 0)
    ]
    if not query:
        return eligible
    q = query.lower()
    filtered = [
        p for p in eligible
        if q in p.get("partner", "").lower()
        or q in p.get("title_th", "")
        or q in p.get("category", "").lower()
    ]
    # If keyword filter yields nothing, return all eligible — better than empty for the UX.
    return filtered or eligible


def _none_result() -> dict:
    return {"action": "none", "upsell": {"package": None, "reason_th": None}}


def _upgrade_to(target_tier: str, reason_th: str) -> dict:
    package = _package_name_for_tier(target_tier)
    if package is None:
        return _none_result()
    return {"action": "upgrade", "upsell": {"package": package, "reason_th": reason_th}}


def decide_action(user_id: str, intent: str, context: dict) -> dict:
    """The policy. Returns {"action": ..., "upsell": {"package", "reason_th"}}.

    Enforces monetization.max_discount_pct: an offered discount can never exceed the ceiling.
    `action` is set HERE, not by the LLM. This is the deterministic governance layer.
    """
    cfg = get_settings()
    if not cfg.monetization.enabled:
        return _none_result()

    tier = user_tier(user_id)

    if intent in {"find_content", "entitlement_check", "live_schedule"}:
        target = context.get("target_min_package")
        if not target:
            return _none_result()
        if TIER_ORDER.get(tier, 0) >= TIER_ORDER.get(target, 99):
            return {"action": "play", "upsell": {"package": None, "reason_th": None}}
        reason = (
            "อัปเกรดเพื่อรับชมพรีเมียร์ลีกและคอนเทนต์ระดับพรีเมียม"
            if target == "PREMIUM"
            else "อัปเกรดเพื่อปลดล็อกคลังคอนเทนต์เต็มรูปแบบและดูได้ 2 จอ"
        )
        return _upgrade_to(target, reason)

    if intent == "find_privilege":
        privileges = context.get("privileges") or []
        if not privileges:
            return _none_result()
        # Enforce the discount ceiling — any offer above max_discount_pct is dropped from
        # the eligible pool. Points-based redemptions (discount_pct=0) always pass.
        ceiling = cfg.monetization.max_discount_pct
        within_limit = [p for p in privileges if int(p.get("discount_pct", 0)) <= ceiling]
        if not within_limit:
            return _none_result()
        top = within_limit[0]
        reason = f"แลกสิทธิ์ {top.get('title_th', '')} ที่ {top.get('partner', '')}"
        return {"action": "redeem", "upsell": {"package": None, "reason_th": reason}}

    if intent == "recommend_package":
        if TIER_ORDER.get(tier, 0) >= TIER_ORDER["PREMIUM"]:
            return _none_result()
        reason = "อัปเกรดเป็น TrueID Premium เพื่อรับชมพรีเมียร์ลีกครบทุกแมตช์และคอนเทนต์ระดับพรีเมียมทั้งหมด"
        return _upgrade_to("PREMIUM", reason)

    return _none_result()
