import pytest


@pytest.mark.skip(reason="TODO(claude-code, Phase 7): hybrid returns relevant ids; degrades to BM25-only with no key")
def test_hybrid_and_bm25_fallback():
    ...
