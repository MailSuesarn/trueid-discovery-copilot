"""OpenAI embeddings + committed on-disk cache (so Colab ingest is offline & instant).

Model: text-embedding-3-large, dims=1024 (config: embeddings.*). See ARCHITECTURE.md §4.
"""
from __future__ import annotations

import numpy as np


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed many docs (called at ingest; result cached to embeddings.cache_path)."""
    raise NotImplementedError("Phase 2: batch OpenAI embeddings, return (n, dims) float32")


def embed_query(text: str) -> "np.ndarray | None":
    """Embed one query at request time. Return None if no OPENAI_API_KEY (dense disabled)."""
    raise NotImplementedError("Phase 2")


def save_cache(path: str, ids: list[str], vectors: np.ndarray) -> None:
    raise NotImplementedError("Phase 2: np.savez(path, ids=ids, vectors=vectors)")


def load_cache(path: str) -> "tuple[list[str], np.ndarray] | None":
    """Load (ids, vectors) from the committed cache; None if the file is absent."""
    raise NotImplementedError("Phase 2")
