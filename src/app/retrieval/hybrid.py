"""Hybrid retriever: BM25 + dense fused with Reciprocal Rank Fusion.

Single `Retriever` interface so the in-memory backend can later be swapped for Qdrant
without touching the orchestrator. Degrades to BM25-only when dense is unavailable
(no key, no cache) — this is what guarantees retrieval works with no key.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from app.core.config import get_settings
from app.retrieval.bm25 import BM25Index
from app.retrieval.dense import DenseIndex
from app.retrieval.embeddings import embed_query, load_cache
from app.retrieval.ingest import Doc, load_docs


@dataclass
class RetrievedDoc:
    id: str          # namespaced, e.g. "catalog:c-014"
    text: str
    score: float
    meta: dict


def _rrf_fuse(rank_lists: list[list[tuple[str, float]]], k: int, rrf_k: int) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for ranked in rank_lists:
        for rank, (doc_id, _) in enumerate(ranked):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rrf_k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]


class Retriever:
    def __init__(self, docs: list[Doc], bm25: BM25Index, dense: DenseIndex | None) -> None:
        self.docs = docs
        self._by_id: dict[str, Doc] = {d.id: d for d in docs}
        self.bm25 = bm25
        self.dense = dense

    @classmethod
    def load(cls) -> Retriever:
        cfg = get_settings()
        docs = load_docs()
        ids = [d.id for d in docs]
        texts = [d.text for d in docs]
        bm25 = BM25Index(ids, texts)

        dense: DenseIndex | None = None
        cached = load_cache(cfg.embeddings.cache_path)
        if cached is not None:
            cached_ids, vectors = cached
            # Align cached vectors with the current doc order (drop any unknowns).
            wanted = {d.id: i for i, d in enumerate(docs)}
            keep_idx = [i for i, cid in enumerate(cached_ids) if cid in wanted]
            if keep_idx:
                ordered_ids = [cached_ids[i] for i in keep_idx]
                ordered_vecs = vectors[keep_idx]
                dense = DenseIndex(ordered_ids, ordered_vecs)
        return cls(docs, bm25, dense)

    def search(self, query: str, top_k: int | None = None) -> list[RetrievedDoc]:
        cfg = get_settings().retrieval
        candidate_k = cfg.candidate_k
        top_k = top_k or cfg.top_k
        if not query.strip():
            return []

        rank_lists: list[list[tuple[str, float]]] = []
        if cfg.hybrid.use_bm25:
            rank_lists.append(self.bm25.search(query, candidate_k))

        if cfg.hybrid.use_dense and self.dense is not None:
            qvec = embed_query(query)
            if qvec is not None:
                rank_lists.append(self.dense.search(qvec, candidate_k))

        # BM25-only fallback when dense is disabled or returns nothing.
        if not rank_lists:
            return []
        fused = _rrf_fuse(rank_lists, top_k, cfg.hybrid.rrf_k)
        out: list[RetrievedDoc] = []
        for doc_id, score in fused:
            doc = self._by_id.get(doc_id)
            if doc is None:
                continue
            out.append(RetrievedDoc(id=doc.id, text=doc.text, score=score, meta=doc.meta))
        return out


@lru_cache
def get_retriever() -> Retriever:
    return Retriever.load()
