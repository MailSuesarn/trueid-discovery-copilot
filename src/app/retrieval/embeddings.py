"""OpenAI embeddings + committed on-disk cache.

The catalog vectors are computed once (with a key) and cached to embeddings.cache_path;
Colab ingest reads the cache and makes NO API call. Only the query is embedded at request
time (one cheap call). If no key is present, `embed_query` returns None → dense disabled.
See ARCHITECTURE.md §4.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from app.core.config import get_settings


def _client():
    """Lazily import OpenAI so the module loads even when the SDK isn't configured."""
    from openai import OpenAI

    return OpenAI()


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed many docs in batches. Called at ingest time when an API key is present."""
    cfg = get_settings().embeddings
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required to (re)build the embedding cache")
    client = _client()
    out: list[list[float]] = []
    BATCH = 96
    for start in range(0, len(texts), BATCH):
        batch = texts[start : start + BATCH]
        resp = client.embeddings.create(
            model=cfg.model,
            input=batch,
            dimensions=cfg.dimensions,
        )
        out.extend(d.embedding for d in resp.data)
    return np.asarray(out, dtype=np.float32)


def embed_query(text: str) -> np.ndarray | None:
    """Embed one query at request time. Returns None when no key (dense disabled)."""
    if not os.getenv("OPENAI_API_KEY"):
        return None
    cfg = get_settings().embeddings
    try:
        resp = _client().embeddings.create(
            model=cfg.model,
            input=[text],
            dimensions=cfg.dimensions,
        )
        return np.asarray(resp.data[0].embedding, dtype=np.float32)
    except Exception:  # noqa: BLE001 — degrade silently to BM25-only
        return None


def save_cache(path: str, ids: list[str], vectors: np.ndarray) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, ids=np.asarray(ids, dtype=object), vectors=vectors.astype(np.float32))


def load_cache(path: str) -> tuple[list[str], np.ndarray] | None:
    p = Path(path)
    if not p.exists():
        return None
    data = np.load(p, allow_pickle=True)
    return list(data["ids"].tolist()), np.asarray(data["vectors"], dtype=np.float32)
