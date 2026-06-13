import pytest


@pytest.mark.skip(reason="TODO(claude-code, Phase 7): entitlement tier logic + privilege policy discount ceiling")
def test_entitlement_and_policy():
    # assert can_play("u_premium", "PREMIUM")["can_play"] is True
    # assert decide_action(...) never exceeds monetization.max_discount_pct
    ...
