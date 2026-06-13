"""Lexical BM25 search (rank-bm25). Pure Python — the always-available offline floor.

Mixed-language tokenizer: ASCII tokens are kept whole; non-ASCII tokens (Thai etc.) are
ALSO emitted as character trigrams. This way Thai phrases match without a Thai word
segmenter while ASCII queries still hit titles, team names, and tags cleanly.
"""
from __future__ import annotations

import re

from rank_bm25 import BM25Okapi

_WORD_RE = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    text = text.lower()
    tokens: list[str] = []
    for word in _WORD_RE.findall(text):
        if all(ord(c) < 128 for c in word):
            tokens.append(word)
            continue
        # Long unbroken Thai (or other non-ASCII) strings make poor whole-word tokens.
        # Emit overlapping character trigrams so phrase fragments match across docs.
        if len(word) < 3:
            tokens.append(word)
            continue
        for i in range(len(word) - 2):
            tokens.append(word[i : i + 3])
    return tokens


class BM25Index:
    def __init__(self, doc_ids: list[str], texts: list[str]) -> None:
        self.doc_ids = doc_ids
        self._tokenized = [tokenize(t) for t in texts]
        self._bm25 = BM25Okapi(self._tokenized)

    def search(self, query: str, k: int) -> list[tuple[str, float]]:
        if not query.strip() or not self.doc_ids:
            return []
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(
            ((i, float(s)) for i, s in enumerate(scores)),
            key=lambda x: x[1],
            reverse=True,
        )
        return [(self.doc_ids[i], s) for i, s in ranked[:k] if s > 0]
