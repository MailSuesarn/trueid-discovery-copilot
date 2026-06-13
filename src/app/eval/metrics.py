"""Eval metrics: retrieval quality, action correctness, grounding, latency, cost.

See ARCHITECTURE.md §8. All pure functions over (predictions, golden).
"""
from __future__ import annotations


def hit_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int = 3) -> float:
    raise NotImplementedError("Phase 6")


def mrr(retrieved_ids: list[str], relevant_ids: list[str]) -> float:
    raise NotImplementedError("Phase 6")


def action_accuracy(pred_actions: list[str], gold_actions: list[str]) -> float:
    """Exact match — deterministic because action comes from the policy, not the LLM."""
    raise NotImplementedError("Phase 6")


def groundedness(citations: list[str], retrieved_ids: list[str]) -> float:
    """Fraction of returned citations that are real ids that were actually retrieved."""
    raise NotImplementedError("Phase 6")


def percentile(values: list[float], p: float) -> float:
    raise NotImplementedError("Phase 6")
