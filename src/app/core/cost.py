"""Token + cost accounting. USD per 1M tokens (OpenAI rates, June 2026)."""
from __future__ import annotations

_PRICES: dict[str, tuple[float, float]] = {  # (input_per_1m, output_per_1m)
    "gpt-5.5": (5.0, 30.0),
    "gpt-5.5-pro": (30.0, 180.0),
    "gpt-5.4": (2.5, 15.0),
    "gpt-5.4-mini": (0.75, 4.5),
    "gpt-5.4-nano": (0.20, 1.25),
}
_EMBED_PRICES: dict[str, float] = {
    "text-embedding-3-large": 0.13,
    "text-embedding-3-small": 0.02,
}


def _match(model: str, table: dict):
    if model in table:
        return table[model]
    for key, val in table.items():  # tolerate dated snapshots e.g. gpt-5.5-2026-04-23
        if model.startswith(key):
            return val
    return None


def cost_for(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    price = _match(model, _PRICES)
    if not price:
        return 0.0
    pin, pout = price
    return (prompt_tokens * pin + completion_tokens * pout) / 1_000_000


def embed_cost_for(model: str, tokens: int) -> float:
    price = _match(model, _EMBED_PRICES)
    return (tokens * price / 1_000_000) if price else 0.0
