"""Load the eval golden set (data/golden.jsonl)."""
from __future__ import annotations

import json
from pathlib import Path

from app.core.config import get_settings


def load_golden(path: str | None = None) -> list[dict]:
    target = Path(path or get_settings().eval.golden_path)
    if not target.exists():
        return []
    return [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]
