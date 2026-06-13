"""Dense vector search: cosine similarity over cached embeddings (numpy)."""
from __future__ import annotations

import numpy as np


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return vectors / norms


class DenseIndex:
    def __init__(self, doc_ids: list[str], vectors: np.ndarray) -> None:
        self.doc_ids = doc_ids
        self.vectors = _normalize(np.asarray(vectors, dtype=np.float32))

    def search(self, query_vector: np.ndarray, k: int) -> list[tuple[str, float]]:
        if self.vectors.size == 0:
            return []
        q = np.asarray(query_vector, dtype=np.float32).reshape(-1)
        qn = np.linalg.norm(q) or 1.0
        q = q / qn
        scores = self.vectors @ q
        top = np.argsort(-scores)[:k]
        return [(self.doc_ids[int(i)], float(scores[int(i)])) for i in top]
