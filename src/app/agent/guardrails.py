"""Guardrail helpers: input limits + 'retrieved text is data' framing (prompt-injection hardening)."""
from __future__ import annotations


def clamp_input(text: str) -> str:
    """Trim to guardrails.max_input_chars."""
    raise NotImplementedError("Phase 5")


def as_safe_context(docs: list) -> str:
    """Render retrieved docs into a <context> block clearly marked as data, not instructions."""
    raise NotImplementedError("Phase 5")
