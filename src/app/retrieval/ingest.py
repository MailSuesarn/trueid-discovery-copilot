"""Load data/*.jsonl into searchable docs and build/persist the indexes.

One record -> one doc with a namespaced id (catalog:* faq:* match:* privilege:*).
Builds BM25 (always) + dense (from committed embedding cache or freshly embedded when
a key is present). See data/README.md for schemas and ARCHITECTURE.md §4.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings

DATA_DIR = Path("data")


@dataclass
class Doc:
    id: str          # namespaced, e.g. "catalog:c-014"
    text: str        # the searchable blob
    meta: dict       # the original record


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# Aliases injected into doc text so common Thai/English phrasings match without a
# Thai word segmenter. Cheap, deterministic, and offline.
_LANG_TAGS = {
    "th": "ไทย thai",
    "en": "อังกฤษ ฝรั่ง english western",
    "ko": "เกาหลี korean kdrama k-drama kpop",
    "ja": "ญี่ปุ่น japanese anime jdrama",
    "zh": "จีน chinese cdrama",
}
_TYPE_TAGS = {
    "series": "ซีรีส์ series",
    "movie": "หนัง ภาพยนตร์ movie film",
    "live": "ช่อง สด live channel",
    "music": "เพลง คอนเสิร์ต music concert",
    "short": "คลิป สั้น clip short highlight",
    "kids": "การ์ตูน เด็ก เด็กเล็ก kids children animation",
}
_COMP_ALIASES = {
    "Premier League": "พรีเมียร์ลีก premier league football ฟุตบอล บอล",
    "La Liga": "ลาลีกา la liga football ฟุตบอล บอล spain spanish",
    "UEFA Champions League": "ยูฟ่า แชมเปียนส์ลีก champions league football ฟุตบอล บอล",
    "Bundesliga": "บุนเดสลีกา bundesliga football ฟุตบอล บอล germany",
    "Serie A": "เซเรียอา serie a football ฟุตบอล บอล italy",
    "Thai League 1": "ไทยลีก thai league football ฟุตบอล บอล thai",
}


def _catalog_text(rec: dict) -> str:
    parts = [
        rec.get("title_th", ""),
        rec.get("title_en", ""),
        " ".join(rec.get("genres") or []),
        " ".join(rec.get("mood") or []),
        " ".join(rec.get("editorial_tags") or []),
        rec.get("synopsis_th", ""),
        rec.get("type", ""),
        _TYPE_TAGS.get(rec.get("type", ""), ""),
        _LANG_TAGS.get(rec.get("language", ""), ""),
    ]
    return " ".join(p for p in parts if p)


def _faq_text(rec: dict) -> str:
    return " ".join([
        rec.get("question_th", ""),
        rec.get("answer_th", ""),
        " ".join(rec.get("tags") or []),
    ])


def _match_text(rec: dict) -> str:
    competition = rec.get("competition", "")
    return " ".join([
        competition,
        _COMP_ALIASES.get(competition, ""),
        rec.get("home_th", ""), "พบ", rec.get("away_th", ""),
        rec.get("home_en", ""), "vs", rec.get("away_en", ""),
        rec.get("channel", ""),
        rec.get("head_to_head_th", ""),
        rec.get("status", ""),
    ])


def _privilege_text(rec: dict) -> str:
    return " ".join([
        rec.get("partner", ""),
        rec.get("title_th", ""),
        rec.get("category", ""),
    ])


def load_docs() -> list[Doc]:
    """Read every data file, namespace ids, and produce a flat list of search docs."""
    docs: list[Doc] = []
    for rec in _read_jsonl(DATA_DIR / "catalog.jsonl"):
        docs.append(Doc(id=f"catalog:{rec['id']}", text=_catalog_text(rec), meta=rec))
    for rec in _read_jsonl(DATA_DIR / "faq.jsonl"):
        docs.append(Doc(id=f"faq:{rec['id']}", text=_faq_text(rec), meta=rec))
    for rec in _read_jsonl(DATA_DIR / "matches.jsonl"):
        docs.append(Doc(id=f"match:{rec['id']}", text=_match_text(rec), meta=rec))
    for rec in _read_jsonl(DATA_DIR / "privileges.jsonl"):
        docs.append(Doc(id=f"privilege:{rec['id']}", text=_privilege_text(rec), meta=rec))
    return docs


def build_index() -> dict:
    """Build BM25 + (optionally) the embedding cache. Returns a summary dict."""
    cfg = get_settings()
    docs = load_docs()
    if not docs:
        return {"docs": 0, "note": "no data — run scripts/generate_data.py first"}

    summary = {
        "docs": len(docs),
        "catalog": sum(1 for d in docs if d.id.startswith("catalog:")),
        "faq": sum(1 for d in docs if d.id.startswith("faq:")),
        "match": sum(1 for d in docs if d.id.startswith("match:")),
        "privilege": sum(1 for d in docs if d.id.startswith("privilege:")),
    }

    # Build embedding cache once when a key is available. The cache file is committed,
    # so Colab ingest sees `cache_exists=True` and skips API calls entirely.
    cache_path = cfg.embeddings.cache_path
    if Path(cache_path).exists():
        summary["embeddings"] = "cache_present"
    elif os.getenv("OPENAI_API_KEY"):
        from app.retrieval.embeddings import embed_texts, save_cache

        ids = [d.id for d in docs]
        vectors = embed_texts([d.text for d in docs])
        save_cache(cache_path, ids, vectors)
        summary["embeddings"] = f"built {len(ids)}x{vectors.shape[1]}"
    else:
        summary["embeddings"] = "skipped (no key, no cache) — BM25-only at query time"
    return summary
