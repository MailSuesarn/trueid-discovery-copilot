"""Build the retrieval index + embedding cache from data/. See ARCHITECTURE.md §4."""
from __future__ import annotations


def main() -> None:
    from app.retrieval.ingest import build_index

    summary = build_index()
    print("ingest complete:", summary)


if __name__ == "__main__":
    main()
