"""Intent classification into the 5 supported intents (+ detected language).

provider mode -> classifier prompt with structured output; mock/extractive -> fast
keyword heuristic so the no-key path still routes correctly.
"""
from __future__ import annotations

INTENTS = ["find_content", "entitlement_check", "live_schedule", "find_privilege", "recommend_package"]


def classify(message: str) -> dict:
    """Return {"intent": <one of INTENTS>, "language": "th"|"en"}."""
    raise NotImplementedError("Phase 5")
