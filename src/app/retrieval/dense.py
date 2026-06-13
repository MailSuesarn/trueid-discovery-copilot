"""Dense vector search: cosine similarity over cached embeddings (numpy/sklearn)."""
from __future__ import annotations

import numpy as np


class DenseIndex:
    def __init__(self, doc_ids: list[str], vectors: np.ndarray) -> None:
        raise NotImplementedError("Phase 2: store normalized vectors")

    def search(self, query_vector: np.ndarray, k: int) -> list[tuple[str, float]]:
        raise NotImplementedError("Phase 2: cosine top-k")
