"""Live-match lookup for the `live_schedule` intent (from matches.jsonl).

Uses a FIXED reference 'now' (no real clock) so the demo is reproducible.
"""
from __future__ import annotations


def find_matches(query: str | None = None) -> list[dict]:
    """Return matches (kickoff, channel, min_package, head-to-head). Optionally filter by team/competition."""
    raise NotImplementedError("Phase 3")
