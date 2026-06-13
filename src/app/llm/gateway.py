"""LLM gateway: ONE entrypoint the orchestrator calls, dispatching on LLM_MODE.

modes: provider (OpenAI; auto-degrades to extractive if no key) | extractive (NO LLM,
deterministic answer from retrieved chunks + policy action) | mock (canned, for tests).
ALWAYS returns a dict matching the schema; never raises to the caller (falls back to
extractive on provider failure). See ARCHITECTURE.md §6.
"""
from __future__ import annotations

from pydantic import BaseModel


def compose(prompt_name: str, variables: dict, schema: type[BaseModel]) -> dict:
    """Produce a schema-valid dict (answer_th, citations, action, upsell)."""
    raise NotImplementedError("Phase 4: dispatch provider/extractive/mock per config.effective_mode")
