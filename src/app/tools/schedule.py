"""Live-match lookup for the `live_schedule` intent (from matches.jsonl).

Uses a FIXED reference 'now' (no real clock) so the demo is reproducible.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path("data")


@lru_cache
def _load_matches() -> list[dict]:
    path = DATA_DIR / "matches.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _haystack(rec: dict) -> str:
    return " ".join([
        rec.get("competition", ""),
        rec.get("home_th", ""), rec.get("away_th", ""),
        rec.get("home_en", ""), rec.get("away_en", ""),
        rec.get("channel", ""),
    ]).lower()


def find_matches(query: str | None = None) -> list[dict]:
    """Return matches. With a query, narrow to those whose team/competition names appear in it."""
    matches = _load_matches()
    if not query:
        return matches
    q = query.lower()
    hits = []
    for m in matches:
        hay = _haystack(m)
        if any(token and token in q for token in hay.split()):
            hits.append(m)
    return hits or matches
