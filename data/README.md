# Synthetic data spec

There is **no real database** in this assessment. All data here is synthetic and
generated deterministically by `scripts/generate_data.py` (seeded, so runs are
reproducible). The generator writes the files below. `scripts/ingest.py` then
builds the retrieval index + embedding cache from them.

> Claude Code: implement `generate_data.py` to emit exactly these schemas. Use a
> fixed random seed. Make Thai fields realistic but invented (do NOT copy real
> TrueID catalog data). ~150 catalog items, package matrix, ~40 privileges,
> ~20 FAQ, ~12 live matches, ~6 user profiles, ~25 golden queries.

All files are JSON Lines (`.jsonl`, one JSON object per line) unless noted.

---

## `catalog.jsonl` (~150 rows) — content the copilot can recommend
```json
{"id": "c-014", "type": "series", "title_th": "ปริศนาแห่งโซล", "title_en": "Seoul Mystery",
 "genres": ["crime", "thriller"], "mood": ["tense", "bingeable"], "duration_min": 60,
 "language": "ko", "subtitle": ["th", "en"], "dub": ["th"], "min_package": "PLUS",
 "editorial_tags": ["k-drama", "top10"], "synopsis_th": "นักสืบโซลไขคดีฆาตกรรมต่อเนื่อง..."}
```
- `type`: one of `movie | series | live | music | short | kids`.
- `min_package`: the lowest tier that can play it — one of `FREE | PLUS | PREMIUM`.
- Spread items across all tiers, several genres/moods, and both Thai and foreign
  language titles (so Thai semantic retrieval is exercised).

## `packages.json` (single JSON object) — the tier matrix
```json
{
  "tiers": ["FREE", "PLUS", "PREMIUM"],
  "packages": [
    {"name": "FREE",    "tier": "FREE",    "price_thb": 0,   "includes": ["ads", "limited_catalog"],
     "live_sports": false, "concurrent_devices": 1},
    {"name": "TrueID+", "tier": "PLUS",    "price_thb": 119, "includes": ["no_ads", "full_catalog"],
     "live_sports": false, "concurrent_devices": 2},
    {"name": "TrueID Premium", "tier": "PREMIUM", "price_thb": 349,
     "includes": ["no_ads", "full_catalog", "live_sports_premier_league"],
     "live_sports": true, "concurrent_devices": 2}
  ]
}
```
- Tier order matters: `FREE < PLUS < PREMIUM`. Entitlement = "user tier >= item min_package".

## `privileges.jsonl` (~40 rows) — deals/rewards
```json
{"id": "p-007", "partner": "Café Amazon", "title_th": "ลด 30 บาท เครื่องดื่มแก้วที่สอง",
 "category": "food", "cost_points": 50, "discount_pct": 0, "min_tier": "FREE",
 "segment": ["all"], "expires": "2026-12-31"}
```
- Mix `cost_points` deals and `discount_pct` deals. `min_tier` gates eligibility.

## `faq.jsonl` (~20 rows) — help content (for grounded answers)
```json
{"id": "f-003", "question_th": "ดูพรีเมียร์ลีกใน TrueID ต้องใช้แพ็กไหน",
 "answer_th": "ต้องเป็นแพ็ก TrueID Premium ขึ้นไป...", "tags": ["sports", "package"]}
```

## `matches.jsonl` (~12 rows) — live sports flagship (static "match facts")
```json
{"id": "m-002", "competition": "Premier League", "home_th": "ลิเวอร์พูล", "away_th": "อาร์เซนอล",
 "home_en": "Liverpool", "away_en": "Arsenal", "kickoff": "2026-06-14T21:30:00+07:00",
 "channel": "TrueID Premium Sport 1", "min_package": "PREMIUM", "status": "scheduled",
 "head_to_head_th": "5 นัดหลังสุด ลิเวอร์พูลชนะ 3 เสมอ 1 แพ้ 1"}
```
- These power the `live_schedule` intent. Kickoffs should be near "today" relative
  to a fixed reference date the generator sets (keep it static/deterministic — do
  NOT use real-time clocks, so the demo is reproducible).

## `users.jsonl` (~6 rows) — synthetic profiles for the entitlement tool
```json
{"user_id": "u_001", "current_package": "TrueID+", "tier": "PLUS",
 "points": 120, "segment": "returning"}
```
- Used by `app/tools/entitlement.py` and the privilege policy. Include at least one
  FREE, one PLUS, one PREMIUM user.

---

## `golden.jsonl` (~25 rows) — eval golden set (handwritten, not auto-generated)
The evaluation ground truth. Each row pairs a query with the expected intent, the
relevant source id(s) for retrieval metrics, and the expected deterministic action.
```json
{"query": "คืนนี้มีบอลพรีเมียร์ลีกไหม ดูได้เลยหรือเปล่า", "user_id": "u_001",
 "expected_intent": "live_schedule", "relevant_ids": ["m-002", "f-003"],
 "expected_action": "upgrade", "language": "th"}
```
- `relevant_ids` -> used for **Hit@3 / MRR** (did retrieval surface the right sources?).
- `expected_action` -> used for **action accuracy** (exact match; deterministic).
- Cover all 5 intents, both languages, and all 3 entitlement outcomes
  (can play -> `play`; needs higher tier + eligible -> `upgrade`; privilege -> `redeem`).

> Claude Code: write `golden.jsonl` BY HAND to match the data you generate (ids must
> line up). This is the single most important file for the eval story — keep it
> consistent with the generated catalog/matches/packages.
