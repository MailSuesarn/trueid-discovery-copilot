"""Metric math: hit@k, mrr, action accuracy, groundedness, percentile."""
from __future__ import annotations

from app.eval.metrics import action_accuracy, groundedness, hit_at_k, mrr, percentile


def test_hit_at_k_namespace_aware():
    assert hit_at_k(["catalog:c-014", "catalog:c-002"], ["c-014"], k=3) == 1.0
    assert hit_at_k(["catalog:c-099"], ["c-014"], k=3) == 0.0


def test_mrr_uses_first_relevant_position():
    assert mrr(["a", "b", "c"], ["c"]) == 1 / 3
    assert mrr(["catalog:c-014"], ["c-014"]) == 1.0
    assert mrr(["catalog:c-001"], ["c-014"]) == 0.0


def test_action_accuracy_exact_match():
    assert action_accuracy(["play", "none"], ["play", "upgrade"]) == 0.5
    assert action_accuracy(["play", "upgrade"], ["play", "upgrade"]) == 1.0


def test_groundedness_treats_unretrieved_citations_as_hallucination():
    retrieved = ["catalog:c-001", "catalog:c-014"]
    assert groundedness(["catalog:c-014"], retrieved) == 1.0
    assert groundedness(["catalog:c-014", "catalog:c-999"], retrieved) == 0.5


def test_percentile_sorted_value():
    assert percentile([10, 20, 30, 40, 50], 50) == 30
    assert percentile([10, 20, 30, 40, 50], 95) == 50
    assert percentile([], 50) == 0.0
