"""Versioned prompt loader. Reads prompts/<name>.v<N>.md and fills {vars}. Never inline prompts in code."""
from __future__ import annotations


def load_prompt(name: str, version: int | None = None) -> str:
    """Return the prompt template text (highest version unless one is requested)."""
    raise NotImplementedError("Phase 4")


def render(name: str, **variables) -> str:
    """load_prompt(name) then .format(**variables)."""
    raise NotImplementedError("Phase 4")
