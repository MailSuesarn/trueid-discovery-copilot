"""Eval metrics: retrieval quality, action correctness, grounding, latency, cost.

See ARCHITECTURE.md §8. All pure functions over (predictions, golden).
"""
from __future__ import annotations


def strip_ns(doc_id: str) -> str:
    """Drop the namespace prefix so 'catalog:c-014' matches the golden's 'c-014'."""
    return doc_id.split(":", 1)[-1]


def hit_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int = 3) -> float:
    if not relevant_ids:
        return 0.0
    head = {strip_ns(i) for i in retrieved_ids[:k]}
    return 1.0 if any(strip_ns(r) in head for r in relevant_ids) else 0.0


def mrr(retrieved_ids: list[str], relevant_ids: list[str]) -> float:
    if not relevant_ids:
        return 0.0
    rel = {strip_ns(r) for r in relevant_ids}
    for rank, rid in enumerate(retrieved_ids, start=1):
        if strip_ns(rid) in rel:
            return 1.0 / rank
    return 0.0


def action_accuracy(pred_actions: list[str], gold_actions: list[str]) -> float:
    if not gold_actions:
        return 0.0
    hits = sum(1 for p, g in zip(pred_actions, gold_actions, strict=False) if p == g)
    return hits / len(gold_actions)


def groundedness(citations: list[str], retrieved_ids: list[str]) -> float:
    """Fraction of returned citations that are real ids that were actually retrieved."""
    if not citations:
        return 0.0
    retrieved = {strip_ns(r) for r in retrieved_ids}
    real = sum(1 for c in citations if strip_ns(c) in retrieved)
    return real / len(citations)


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1)))))
    return s[k]
