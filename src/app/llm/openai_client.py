"""Thin OpenAI wrapper with PER-FAMILY parameter handling + structured output + retries.

CRITICAL (verified June 2026): gpt-5.x / o* are REASONING models — do NOT send
`temperature`/`top_p`; use `max_completion_tokens` (chat) / `max_output_tokens` (responses);
steer with `reasoning_effort` + `verbosity`. Structured output via responses.parse(text_format=Model)
with a chat.completions.parse fallback. Wrap in tenacity retry + timeout. See ARCHITECTURE.md §6.
"""
from __future__ import annotations

from pydantic import BaseModel


def is_reasoning_model(model: str) -> bool:
    return model.startswith(("gpt-5", "o1", "o3", "o4"))


def build_params(model: str, max_output_tokens: int, reasoning_effort: str, verbosity: str) -> dict:
    """Return the kwargs appropriate for this model family (no temperature for reasoning models)."""
    raise NotImplementedError("Phase 4")


def structured_complete(model: str, messages: list[dict], schema: type[BaseModel]):
    """Call OpenAI and return an instance of `schema`. responses.parse first, chat fallback."""
    raise NotImplementedError("Phase 4")
