"""Run the pipeline over the golden set and report the metrics table.

`python -m app.eval.run_eval`         -> print the table
`python -m app.eval.run_eval --check` -> exit non-zero if below eval.thresholds (CI gate)
See ARCHITECTURE.md §8.
"""
from __future__ import annotations

import sys
import time

from app.api.schemas import ChatRequest
from app.core.config import get_settings
from app.eval.golden import load_golden
from app.eval.metrics import action_accuracy, groundedness, hit_at_k, mrr, percentile
from app.llm.gateway import last_usage
from app.retrieval.hybrid import get_retriever


def run() -> dict:
    """Execute the full pipeline over every golden row and aggregate metrics."""
    from app.agent.orchestrator import handle_chat  # avoid circular import at module load

    golden = load_golden()
    if not golden:
        return {"note": "no golden set found"}

    retriever = get_retriever()
    hits_3, mrrs, pred_actions, gold_actions, grounds = [], [], [], [], []
    latencies_ms: list[float] = []
    costs: list[float] = []

    for row in golden:
        gold_actions.append(row["expected_action"])
        retrieved_docs = retriever.search(row["query"])
        retrieved_ids = [d.id for d in retrieved_docs]
        hits_3.append(hit_at_k(retrieved_ids, row["relevant_ids"], k=3))
        mrrs.append(mrr(retrieved_ids, row["relevant_ids"]))

        t0 = time.perf_counter()
        resp = handle_chat(ChatRequest(user_id=row["user_id"], message=row["query"]))
        latencies_ms.append((time.perf_counter() - t0) * 1000)
        pred_actions.append(resp.action)
        grounds.append(groundedness(resp.citations, retrieved_ids))
        costs.append(float(last_usage().get("cost_usd", 0.0)))

    n = len(golden)
    return {
        "n": n,
        "hit_at_3": round(sum(hits_3) / n, 4),
        "mrr": round(sum(mrrs) / n, 4),
        "action_accuracy": round(action_accuracy(pred_actions, gold_actions), 4),
        "groundedness": round(sum(grounds) / n, 4),
        "latency_p50_ms": round(percentile(latencies_ms, 50), 2),
        "latency_p95_ms": round(percentile(latencies_ms, 95), 2),
        "cost_per_query_usd": round(sum(costs) / n, 6),
    }


def _enforce_thresholds(results: dict) -> int:
    thresholds = get_settings().eval.thresholds
    failures: list[str] = []
    if results["hit_at_3"] < thresholds.hit_at_3:
        failures.append(f"hit_at_3 {results['hit_at_3']} < {thresholds.hit_at_3}")
    if results["action_accuracy"] < thresholds.action_accuracy:
        failures.append(f"action_accuracy {results['action_accuracy']} < {thresholds.action_accuracy}")
    if results["groundedness"] < thresholds.groundedness:
        failures.append(f"groundedness {results['groundedness']} < {thresholds.groundedness}")
    if failures:
        print("FAIL:", "; ".join(failures))
        return 1
    print("OK: all thresholds met")
    return 0


def main() -> None:
    check = "--check" in sys.argv
    results = run()
    for key, value in results.items():
        print(f"{key:>22}: {value}")
    if check:
        sys.exit(_enforce_thresholds(results))


if __name__ == "__main__":
    main()
