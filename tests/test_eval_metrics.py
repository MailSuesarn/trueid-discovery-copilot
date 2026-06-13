import pytest


@pytest.mark.skip(reason="TODO(claude-code, Phase 7): metric math on tiny fixtures (hit@k, mrr, action acc, groundedness)")
def test_metric_math():
    # assert hit_at_k(["a", "b", "c"], ["c"], k=3) == 1.0
    # assert action_accuracy(["play", "none"], ["play", "upgrade"]) == 0.5
    ...
