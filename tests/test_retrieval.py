"""Hybrid returns relevant ids; the system degrades to BM25-only without a key."""
from __future__ import annotations

import os

from app.retrieval.bm25 import BM25Index
from app.retrieval.embeddings import embed_query
from app.retrieval.hybrid import Retriever


def test_no_key_disables_query_embedding():
    # The real degrade switch: with no key, the query is never embedded, so dense search is
    # skipped at query time even if a committed vector cache loaded a dense index. This is
    # what guarantees the no-key path works regardless of whether embeddings.npz is present.
    assert "OPENAI_API_KEY" not in os.environ
    assert embed_query("ซีรีส์เกาหลี") is None


def test_retrieval_returns_relevant_ids_without_key():
    retriever = Retriever.load()
    th = retriever.search("ซีรีส์เกาหลีนักสืบ", top_k=5)
    en = retriever.search("Premier League tonight", top_k=5)
    assert th and en
    assert {"catalog:c-014"} & {d.id for d in th}, "Seoul Mystery should rank for the TH query"
    assert any(d.id.startswith("match:") for d in en), "PL query should surface match docs"


def test_bm25_index_pure_tokenization():
    # rank-bm25 IDF goes to 0 when a term appears in exactly half of a tiny corpus,
    # so a small but non-trivial collection is needed to see a real ranking.
    idx = BM25Index(
        ["a", "b", "c", "d"],
        [
            "liverpool arsenal football",
            "ราคาแพ็ก premium",
            "manchester united football",
            "ดาวเคราะห์สาบสูญ planet",
        ],
    )
    ranked = idx.search("arsenal", k=5)
    assert ranked and ranked[0][0] == "a"
