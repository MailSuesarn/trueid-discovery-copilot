"""Run the pipeline over the golden set and report the metrics table.

`python -m app.eval.run_eval`         -> print the table
`python -m app.eval.run_eval --check` -> exit non-zero if below eval.thresholds (CI gate)
See ARCHITECTURE.md §8.
"""
from __future__ import annotations

import sys


def run() -> dict:
    """Return {"hit_at_3":..., "mrr":..., "action_accuracy":..., "groundedness":...,
    "latency_p50_ms":..., "latency_p95_ms":..., "cost_per_query_usd":...}."""
    raise NotImplementedError("Phase 6")


def main() -> None:
    check = "--check" in sys.argv
    results = run()
    for key, value in results.items():
        print(f"{key:>22}: {value}")
    if check:
        raise NotImplementedError("Phase 6: compare to eval.thresholds and sys.exit(1) on failure")


if __name__ == "__main__":
    main()
