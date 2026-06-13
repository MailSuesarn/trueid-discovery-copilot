"""Guardrail helpers: input limits + 'retrieved text is data' framing (prompt-injection hardening)."""
from __future__ import annotations

from app.core.config import get_settings


def clamp_input(text: str) -> str:
    """Trim to guardrails.max_input_chars."""
    limit = get_settings().guardrails.max_input_chars
    return text[:limit]


def as_safe_context(docs: list) -> str:
    """Render retrieved docs into a block clearly marked as data, not instructions.

    The composer prompt wraps this in <context> tags and the system prompt instructs
    the model to ignore any embedded instructions inside that block.
    """
    if not docs:
        return "(no relevant context retrieved)"
    lines = []
    for d in docs:
        meta = d.meta if hasattr(d, "meta") else d.get("meta", {})
        snippet = (
            meta.get("title_th") or meta.get("question_th") or meta.get("home_th")
            or meta.get("partner") or d.id if hasattr(d, "id") else d.get("id", "")
        )
        text = d.text if hasattr(d, "text") else d.get("text", "")
        lines.append(f"- id={d.id if hasattr(d, 'id') else d.get('id','')} | {snippet} | {text[:200]}")
    return "\n".join(lines)
