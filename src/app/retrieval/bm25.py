"""Lexical BM25 search (rank-bm25). Pure Python — the always-available offline floor."""
from __future__ import annotations


class BM25Index:
    """Build over doc texts; query returns ranked (doc_id, score)."""

    def __init__(self, doc_ids: list[str], texts: list[str]) -> None:
        raise NotImplementedError("Phase 2: tokenize + build rank_bm25.BM25Okapi")

    def search(self, query: str, k: int) -> list[tuple[str, float]]:
        raise NotImplementedError("Phase 2")
