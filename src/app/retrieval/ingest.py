"""Load data/*.jsonl into searchable docs and build/persist the indexes.

One record -> one doc with a namespaced id (catalog:* faq:* match:* privilege:*).
Builds BM25 + dense (from committed embedding cache or freshly embedded), persists to
data/index/. See data/README.md for schemas and ARCHITECTURE.md §4.
"""
from __future__ import annotations


def build_index() -> dict:
    """Run ingestion; return a summary dict (counts per source). Print it in scripts/ingest.py."""
    raise NotImplementedError("Phase 2")
