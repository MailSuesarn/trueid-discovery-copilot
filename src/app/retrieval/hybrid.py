"""Hybrid retriever: BM25 + dense fused with Reciprocal Rank Fusion.

Single `Retriever` interface so the in-memory backend can later be swapped for Qdrant
without touching the orchestrator. Degrades to BM25-only when dense is unavailable
(no key / no cache) — this is what guarantees retrieval works with no key.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetrievedDoc:
    id: str          # namespaced, e.g. "catalog:c-014"
    text: str
    score: float
    meta: dict


class Retriever:
    @classmethod
    def load(cls) -> "Retriever":
        """Load persisted BM25 + dense indexes built by app.retrieval.ingest."""
        raise NotImplementedError("Phase 2")

    def search(self, query: str, top_k: int | None = None) -> list[RetrievedDoc]:
        """RRF over BM25 (+ dense if available). Returns top_k grounded docs."""
        raise NotImplementedError("Phase 2: RRF fusion with rrf_k from config")
