"""Versioned prompt loader. Reads prompts/<name>.v<N>.md and fills {vars}. Never inline prompts in code."""
from __future__ import annotations

import re
from pathlib import Path

PROMPTS_DIR = Path("prompts")
_VERSION_RE = re.compile(r"^(?P<name>.+)\.v(?P<ver>\d+)\.md$")


def _candidates(name: str) -> list[tuple[int, Path]]:
    out: list[tuple[int, Path]] = []
    for p in PROMPTS_DIR.glob(f"{name}.v*.md"):
        m = _VERSION_RE.match(p.name)
        if m and m.group("name") == name:
            out.append((int(m.group("ver")), p))
    return out


def load_prompt(name: str, version: int | None = None) -> str:
    matches = _candidates(name)
    if not matches:
        raise FileNotFoundError(f"no prompt found for {name!r} in {PROMPTS_DIR}")
    if version is not None:
        for ver, p in matches:
            if ver == version:
                return p.read_text(encoding="utf-8")
        raise FileNotFoundError(f"prompt {name!r} v{version} not found")
    matches.sort(reverse=True)
    return matches[0][1].read_text(encoding="utf-8")


def render(name: str, **variables: object) -> str:
    template = load_prompt(name)
    # Use str.replace to avoid choking on stray { } inside example blocks.
    for key, value in variables.items():
        template = template.replace("{" + key + "}", str(value))
    return template
