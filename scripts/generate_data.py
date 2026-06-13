"""Generate deterministic synthetic data into data/. Schemas: data/README.md.

TODO(claude-code, Phase 1): seeded generation of catalog (~150), packages, privileges
(~40), faq (~20), matches (~12), users (~6). Invent realistic Thai text (do NOT copy real
TrueID data). Then hand-write data/golden.jsonl so ids line up.
"""
from __future__ import annotations


def main() -> None:
    raise NotImplementedError("Phase 1: emit data/*.jsonl per data/README.md")


if __name__ == "__main__":
    main()
