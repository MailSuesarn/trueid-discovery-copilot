"""Generate deterministic synthetic data into data/. Schemas: data/README.md.

Seeded so runs are reproducible. All Thai text is invented (no real TrueID catalog
data is copied). Writes catalog.jsonl (~150), packages.json, privileges.jsonl (~40),
faq.jsonl (~20), matches.jsonl (~12), users.jsonl (~6). The golden.jsonl file is
hand-written so ids line up with the anchors emitted here.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

SEED = 42
DATA_DIR = Path("data")

# Fixed reference "now" — keeps the live-schedule demo reproducible. The data
# generator does NOT consult a real clock.
REFERENCE_DATE = "2026-06-14"  # used to anchor `kickoff` timestamps in matches


# =============================================================================
# Catalog (~150 items). Anchors first (referenced by golden.jsonl); template
# items fill the rest with varied genres, languages, tiers, and moods.
# =============================================================================
CATALOG_ANCHORS: list[dict] = [
    # --- K-drama / J-drama / C-drama (referenced by golden) ---
    {"id": "c-014", "type": "series", "title_th": "ปริศนาแห่งโซล", "title_en": "Seoul Mystery",
     "genres": ["crime", "thriller", "mystery"], "mood": ["tense", "bingeable"],
     "duration_min": 60, "language": "ko", "subtitle": ["th", "en"], "dub": ["th"],
     "min_package": "PLUS", "editorial_tags": ["k-drama", "top10", "detective"],
     "synopsis_th": "นักสืบโซลไขคดีฆาตกรรมต่อเนื่องที่เกี่ยวพันกับอดีตอันลึกลับของตนเอง บรรยากาศหนาวเหน็บ ดูเพลินก่อนนอน"},
    {"id": "c-015", "type": "series", "title_th": "ราตรีรักโตเกียว", "title_en": "Tokyo Nights",
     "genres": ["romance", "drama"], "mood": ["romantic", "bingeable"],
     "duration_min": 55, "language": "ja", "subtitle": ["th", "en"], "dub": ["th"],
     "min_package": "PLUS", "editorial_tags": ["j-drama", "romance"],
     "synopsis_th": "เชฟสาวพบรักครั้งใหม่ในร้านราเมงเล็กๆ ย่านชิบุยะ"},
    {"id": "c-016", "type": "series", "title_th": "นักสืบเซี่ยงไฮ้", "title_en": "Shanghai Detective",
     "genres": ["crime", "mystery"], "mood": ["tense", "cinematic"],
     "duration_min": 50, "language": "zh", "subtitle": ["th", "en"], "dub": ["th"],
     "min_package": "PLUS", "editorial_tags": ["c-drama", "detective"],
     "synopsis_th": "ทีมนักสืบจีนไขคดีลึกลับในเซี่ยงไฮ้ยุคปี 1930"},

    # --- Thai content ---
    {"id": "c-001", "type": "movie", "title_th": "บ้านเรามีรัก", "title_en": "A Family Tale",
     "genres": ["family", "drama"], "mood": ["light", "feel_good"],
     "duration_min": 95, "language": "th", "subtitle": ["en"], "dub": [],
     "min_package": "FREE", "editorial_tags": ["thai", "family", "short"],
     "synopsis_th": "เรื่องราวอบอุ่นของครอบครัวเล็กๆ ในบ้านไม้ริมคลอง เหมาะดูกับลูกหลานช่วงเย็น"},
    {"id": "c-002", "type": "series", "title_th": "เพชรกลางบ้าน", "title_en": "Diamond at Home",
     "genres": ["drama", "romance"], "mood": ["bingeable", "romantic"],
     "duration_min": 60, "language": "th", "subtitle": ["en"], "dub": [],
     "min_package": "PLUS", "editorial_tags": ["thai", "lakorn", "top10"],
     "synopsis_th": "ละครรักดราม่าครอบครัวใหญ่ที่ซ่อนความลับร้ายแรงไว้หลังประตู"},
    {"id": "c-003", "type": "movie", "title_th": "ผีบ้านหลังนั้น", "title_en": "House of Spirits",
     "genres": ["horror", "thriller"], "mood": ["scary", "tense"],
     "duration_min": 105, "language": "th", "subtitle": ["en"], "dub": [],
     "min_package": "PLUS", "editorial_tags": ["thai", "horror", "halloween"],
     "synopsis_th": "บ้านเก่ากลางทุ่งเก็บความลับสยองที่ครอบครัวใหม่ต้องเจอ น่ากลัวระดับโรงหนัง"},
    {"id": "c-004", "type": "series", "title_th": "รักนี้คือลิขิต", "title_en": "Fated Love",
     "genres": ["romance", "drama"], "mood": ["romantic", "feel_good"],
     "duration_min": 55, "language": "th", "subtitle": ["en"], "dub": [],
     "min_package": "PLUS", "editorial_tags": ["thai", "lakorn", "romance"],
     "synopsis_th": "ซีรีส์ไทยรักโรแมนติกของหนุ่มสาวที่บังเอิญพบกันบนรถไฟฟ้า"},

    # --- Anime ---
    {"id": "c-040", "type": "series", "title_th": "ดาบเทพแห่งทาเครุ", "title_en": "Takeru's Divine Blade",
     "genres": ["action", "fantasy"], "mood": ["epic", "tense"],
     "duration_min": 24, "language": "ja", "subtitle": ["th", "en"], "dub": ["th"],
     "min_package": "PLUS", "editorial_tags": ["anime", "shounen", "action"],
     "synopsis_th": "อนิเมะแอคชั่นเข้มข้น พระเอกฝึกดาบศักดิ์สิทธิ์ปราบมาร เปิดศึกระดับเทพ"},
    {"id": "c-041", "type": "series", "title_th": "นักล่าไคจูเมืองโอซาก้า", "title_en": "Osaka Kaiju Hunters",
     "genres": ["action", "sci-fi"], "mood": ["epic", "tense"],
     "duration_min": 24, "language": "ja", "subtitle": ["th", "en"], "dub": ["th"],
     "min_package": "PLUS", "editorial_tags": ["anime", "action", "scifi"],
     "synopsis_th": "หน่วยล่าไคจูแห่งโอซาก้าปกป้องเมืองจากสัตว์ประหลาดข้ามมิติ"},

    # --- Kids ---
    {"id": "c-060", "type": "kids", "title_th": "หมีน้อยใจดี", "title_en": "Little Kind Bear",
     "genres": ["animation", "family", "educational"], "mood": ["wholesome", "fun"],
     "duration_min": 20, "language": "th", "subtitle": [], "dub": ["en"],
     "min_package": "FREE", "editorial_tags": ["kids", "preschool"],
     "synopsis_th": "การ์ตูนเด็กเล็กสอนเรื่องการแบ่งปันและมิตรภาพ พากย์ไทย เหมาะวัย 3-7 ขวบ"},
    {"id": "c-061", "type": "kids", "title_th": "ผจญภัยในป่าสีรุ้ง", "title_en": "Rainbow Forest Adventure",
     "genres": ["animation", "family"], "mood": ["wholesome", "fun"],
     "duration_min": 25, "language": "th", "subtitle": [], "dub": ["en"],
     "min_package": "FREE", "editorial_tags": ["kids", "animation"],
     "synopsis_th": "สามเพื่อนสัตว์ออกผจญภัยในป่าสีรุ้งเพื่อตามหาดอกไม้วิเศษ"},

    # --- Western movies / series ---
    {"id": "c-080", "type": "movie", "title_th": "เงาราตรีในลอนดอน", "title_en": "London Shadows",
     "genres": ["thriller", "crime"], "mood": ["tense", "cinematic"],
     "duration_min": 118, "language": "en", "subtitle": ["th"], "dub": ["th"],
     "min_package": "PLUS", "editorial_tags": ["western", "thriller"],
     "synopsis_th": "นักสืบลอนดอนถูกบีบให้รับคดีฆาตกรรมที่เกี่ยวข้องกับอดีตของตัวเอง"},
    {"id": "c-081", "type": "series", "title_th": "หน่วยพิเศษนิวยอร์ก", "title_en": "NYC Special Unit",
     "genres": ["crime", "drama"], "mood": ["bingeable", "tense"],
     "duration_min": 45, "language": "en", "subtitle": ["th"], "dub": ["th"],
     "min_package": "PLUS", "editorial_tags": ["western", "procedural"],
     "synopsis_th": "ซีรีส์ตำรวจอเมริกัน ทีมพิเศษจับอาชญากรไซเบอร์ในนิวยอร์ก"},
    {"id": "c-082", "type": "movie", "title_th": "ดาวเคราะห์สาบสูญ", "title_en": "Lost Planet",
     "genres": ["sci-fi", "action"], "mood": ["epic", "cinematic"],
     "duration_min": 132, "language": "en", "subtitle": ["th"], "dub": ["th"],
     "min_package": "PREMIUM", "editorial_tags": ["blockbuster", "scifi"],
     "synopsis_th": "นักบินอวกาศต้องอยู่รอดบนดาวเคราะห์ที่ระบบนำทางสาบสูญ ภาพยนตร์ไซไฟระดับโรงหนัง"},

    # --- Live channels ---
    {"id": "c-100", "type": "live", "title_th": "ช่อง TrueID Sport 1", "title_en": "TrueID Sport 1",
     "genres": ["sports"], "mood": ["live"],
     "duration_min": 0, "language": "th", "subtitle": [], "dub": [],
     "min_package": "PREMIUM", "editorial_tags": ["live", "premier_league"],
     "synopsis_th": "ช่องถ่ายทอดสดพรีเมียร์ลีกหลัก พร้อมรายการวิเคราะห์ก่อน-หลังเกม"},
    {"id": "c-101", "type": "live", "title_th": "ช่อง TrueID Sport 2", "title_en": "TrueID Sport 2",
     "genres": ["sports"], "mood": ["live"],
     "duration_min": 0, "language": "th", "subtitle": [], "dub": [],
     "min_package": "PREMIUM", "editorial_tags": ["live", "champions_league"],
     "synopsis_th": "ช่องถ่ายทอดสดแชมเปียนส์ลีกและฟุตบอลยุโรปอื่นๆ"},
    {"id": "c-102", "type": "live", "title_th": "ช่อง TrueID Thai League", "title_en": "TrueID Thai League",
     "genres": ["sports"], "mood": ["live"],
     "duration_min": 0, "language": "th", "subtitle": [], "dub": [],
     "min_package": "PLUS", "editorial_tags": ["live", "thai_football"],
     "synopsis_th": "ช่องถ่ายทอดสดไทยลีก 1 ครบทุกแมตช์"},

    # --- Music ---
    {"id": "c-120", "type": "music", "title_th": "คอนเสิร์ตป๊อปไทย 2026", "title_en": "Thai Pop Live 2026",
     "genres": ["concert"], "mood": ["energetic"],
     "duration_min": 110, "language": "th", "subtitle": [], "dub": [],
     "min_package": "PLUS", "editorial_tags": ["concert", "thai_pop"],
     "synopsis_th": "คอนเสิร์ตป๊อปไทย รวมศิลปินดังถ่ายทอดจากอิมแพ็คอารีน่า"},
    {"id": "c-121", "type": "music", "title_th": "K-Pop Weekend", "title_en": "K-Pop Weekend",
     "genres": ["mv"], "mood": ["energetic", "fun"],
     "duration_min": 90, "language": "ko", "subtitle": ["th"], "dub": [],
     "min_package": "FREE", "editorial_tags": ["k-pop", "playlist"],
     "synopsis_th": "รวม MV เพลงเกาหลีฮิตประจำสัปดาห์"},

    # --- Short ---
    {"id": "c-130", "type": "short", "title_th": "ไฮไลท์ฟุตบอลโลก", "title_en": "World Cup Highlights",
     "genres": ["highlight"], "mood": ["energetic"],
     "duration_min": 8, "language": "th", "subtitle": [], "dub": [],
     "min_package": "FREE", "editorial_tags": ["short", "sports"],
     "synopsis_th": "ไฮไลท์สั้นๆ ของฟุตบอลโลกเอเชี่ยน รวบประตูทั้งหมด"},
]


# Template pieces to expand to ~150
_THAI_ADJ = ["ลึกลับ", "อบอุ่น", "เข้มข้น", "สนุกสนาน", "หวาน", "น่ากลัว", "ตื่นเต้น", "ตลก", "เศร้า", "ผจญภัย"]
_THAI_NOUN = ["เมือง", "ป่า", "ทะเล", "หมู่บ้าน", "บ้าน", "โรงเรียน", "ภูเขา", "ตลาด", "ถนน", "เกาะ"]
_EN_ADJ = ["Hidden", "Bright", "Silent", "Crimson", "Golden", "Frozen", "Endless", "Lost", "Iron", "Velvet"]
_EN_NOUN = ["River", "Forest", "Sky", "Heart", "Promise", "Dragon", "Code", "Empire", "Mirror", "Echo"]

_TYPE_DIST: list[tuple[str, int]] = [
    ("series", 60), ("movie", 50), ("kids", 12), ("music", 8), ("short", 8), ("live", 3),
]
# tiers distribution across template items: FREE 25 / PLUS 55 / PREMIUM 20
_TIER_DIST = (["FREE"] * 25) + (["PLUS"] * 55) + (["PREMIUM"] * 20)
_LANG_DIST = (["th"] * 4) + (["en"] * 3) + (["ko"] * 2) + (["ja"] * 1) + (["zh"] * 1)

_GENRES_BY_TYPE = {
    "movie":  ["action", "comedy", "drama", "romance", "thriller", "horror", "sci-fi", "family"],
    "series": ["crime", "thriller", "romance", "drama", "comedy", "fantasy", "mystery", "action"],
    "live":   ["sports", "news", "variety"],
    "music":  ["concert", "mv"],
    "short":  ["highlight", "clip", "recap"],
    "kids":   ["animation", "family", "educational"],
}
_MOOD_BY_GENRE = {
    "action": ["epic", "tense"],
    "comedy": ["light", "fun"],
    "drama": ["bingeable", "feel_good"],
    "romance": ["romantic", "warm"],
    "thriller": ["tense", "edge_of_seat"],
    "horror": ["scary", "creepy"],
    "sci-fi": ["epic", "cinematic"],
    "family": ["wholesome", "feel_good"],
    "crime": ["tense", "bingeable"],
    "fantasy": ["epic", "cinematic"],
    "mystery": ["tense", "bingeable"],
    "sports": ["live"],
    "news": ["live"],
    "variety": ["fun", "light"],
    "concert": ["energetic"],
    "mv": ["energetic", "fun"],
    "highlight": ["energetic"],
    "clip": ["fun"],
    "recap": ["light"],
    "animation": ["wholesome", "fun"],
    "educational": ["wholesome", "calm"],
}


def _gen_catalog(rng: random.Random) -> list[dict]:
    items: list[dict] = list(CATALOG_ANCHORS)
    used_ids: set[str] = {it["id"] for it in items}

    # Determine the starting numeric id for templated content per type-bucket.
    next_id = 200  # anchors live in c-001..c-130; templated start at c-200+
    flat_types: list[str] = []
    for t, n in _TYPE_DIST:
        flat_types.extend([t] * n)
    rng.shuffle(flat_types)

    for ctype in flat_types:
        if len(items) >= 150:
            break
        item_id = f"c-{next_id:03d}"
        next_id += 1
        while item_id in used_ids:
            item_id = f"c-{next_id:03d}"
            next_id += 1
        used_ids.add(item_id)

        primary_genre = rng.choice(_GENRES_BY_TYPE[ctype])
        extra_genre = rng.choice(_GENRES_BY_TYPE[ctype])
        genres = sorted({primary_genre, extra_genre})
        moods = _MOOD_BY_GENRE.get(primary_genre, ["light"])
        lang = rng.choice(_LANG_DIST) if ctype not in {"live", "music", "short", "kids"} else (
            "th" if ctype in {"live", "short", "kids"} else rng.choice(["th", "ko", "en"])
        )
        tier = rng.choice(_TIER_DIST) if ctype != "live" else "PREMIUM"

        if lang == "th":
            title_th = f"{rng.choice(_THAI_NOUN)}{rng.choice(_THAI_ADJ)}"
            title_en = f"{rng.choice(_EN_ADJ)} {rng.choice(_EN_NOUN)}"
        else:
            title_en = f"{rng.choice(_EN_ADJ)} {rng.choice(_EN_NOUN)}"
            title_th = f"{rng.choice(_THAI_NOUN)}{rng.choice(_THAI_ADJ)}"

        subtitle = ["th", "en"] if lang != "th" else ["en"]
        dub = ["th"] if lang in {"en", "ko", "ja", "zh"} and rng.random() < 0.6 else []
        duration = {
            "movie": rng.randint(85, 145),
            "series": rng.randint(40, 65),
            "kids": rng.randint(15, 30),
            "music": rng.randint(45, 120),
            "short": rng.randint(3, 15),
            "live": 0,
        }[ctype]

        synopsis = (
            f"เรื่องราว{rng.choice(_THAI_ADJ)}ในแบบ{primary_genre} "
            f"ที่เกิดขึ้นใน{rng.choice(_THAI_NOUN)} ดูสนุกในแบบ{moods[0]}"
        )

        items.append({
            "id": item_id,
            "type": ctype,
            "title_th": title_th,
            "title_en": title_en,
            "genres": genres,
            "mood": list(moods),
            "duration_min": duration,
            "language": lang,
            "subtitle": subtitle,
            "dub": dub,
            "min_package": tier,
            "editorial_tags": [primary_genre, ctype],
            "synopsis_th": synopsis,
        })

    return items


# =============================================================================
# Packages (single JSON)
# =============================================================================
PACKAGES = {
    "tiers": ["FREE", "PLUS", "PREMIUM"],
    "packages": [
        {"name": "FREE", "tier": "FREE", "price_thb": 0,
         "includes": ["ads", "limited_catalog"],
         "live_sports": False, "concurrent_devices": 1},
        {"name": "TrueID+", "tier": "PLUS", "price_thb": 119,
         "includes": ["no_ads", "full_catalog"],
         "live_sports": False, "concurrent_devices": 2},
        {"name": "TrueID Premium", "tier": "PREMIUM", "price_thb": 349,
         "includes": ["no_ads", "full_catalog", "live_sports_premier_league"],
         "live_sports": True, "concurrent_devices": 2},
    ],
}


# =============================================================================
# Privileges (~40)
# =============================================================================
PRIVILEGE_ANCHORS: list[dict] = [
    {"id": "p-007", "partner": "Café Amazon", "title_th": "ลด 30 บาท เครื่องดื่มแก้วที่สอง",
     "category": "food", "cost_points": 50, "discount_pct": 0, "min_tier": "FREE",
     "segment": ["all"], "expires": "2026-12-31"},
    {"id": "p-001", "partner": "Café Amazon", "title_th": "แลกกาแฟอเมริกาโน่ฟรี 1 แก้ว",
     "category": "food", "cost_points": 100, "discount_pct": 0, "min_tier": "FREE",
     "segment": ["all"], "expires": "2026-12-31"},
    {"id": "p-002", "partner": "Major Cineplex", "title_th": "แลกตั๋วหนังราคาพิเศษ 50 บาท",
     "category": "entertainment", "cost_points": 80, "discount_pct": 0, "min_tier": "PLUS",
     "segment": ["movie_lover"], "expires": "2026-12-31"},
    {"id": "p-003", "partner": "Tops", "title_th": "ส่วนลด 15% สำหรับสมาชิก",
     "category": "shopping", "cost_points": 0, "discount_pct": 15, "min_tier": "PLUS",
     "segment": ["all"], "expires": "2026-12-31"},
    {"id": "p-004", "partner": "BigC", "title_th": "ส่วนลด 10% เมื่อช้อปครบ 500 บาท",
     "category": "shopping", "cost_points": 0, "discount_pct": 10, "min_tier": "FREE",
     "segment": ["all"], "expires": "2026-12-31"},
    {"id": "p-005", "partner": "Starbucks", "title_th": "ลด 20 บาท เครื่องดื่มขนาด tall",
     "category": "food", "cost_points": 40, "discount_pct": 0, "min_tier": "FREE",
     "segment": ["all"], "expires": "2026-12-31"},
    {"id": "p-006", "partner": "AirAsia", "title_th": "ส่วนลด 200 บาทตั๋วบินในประเทศ",
     "category": "travel", "cost_points": 0, "discount_pct": 5, "min_tier": "PREMIUM",
     "segment": ["traveler"], "expires": "2026-12-31"},
]

_PARTNERS_BY_CAT = {
    "food":          ["McDonald's", "KFC", "Pizza Hut", "Swensen's", "MK", "Yayoi", "Sukishi", "Black Canyon"],
    "shopping":      ["Lazada", "Shopee", "Central", "Robinson", "JD Central", "Tops", "Watson"],
    "travel":        ["Bangkok Airways", "Nok Air", "Agoda", "Booking.com"],
    "entertainment": ["SF Cinema", "Major Cineplex", "House of Music"],
    "telco":         ["True Mobile", "TrueOnline"],
    "lifestyle":     ["Fitness First", "Virgin Active", "Let's Relax Spa"],
}


def _gen_privileges(rng: random.Random) -> list[dict]:
    items: list[dict] = list(PRIVILEGE_ANCHORS)
    used_ids: set[str] = {it["id"] for it in items}
    next_id = 10
    while len(items) < 40:
        pid = f"p-{next_id:03d}"
        next_id += 1
        if pid in used_ids:
            continue
        used_ids.add(pid)
        cat = rng.choice(list(_PARTNERS_BY_CAT.keys()))
        partner = rng.choice(_PARTNERS_BY_CAT[cat])
        # Either points-based redemption OR a discount, not both.
        if rng.random() < 0.5:
            cost_points = rng.choice([30, 50, 80, 100, 150])
            discount_pct = 0
            title_th = f"แลกของรางวัลพิเศษจาก {partner}"
        else:
            cost_points = 0
            discount_pct = rng.choice([5, 10, 15, 20])
            title_th = f"ส่วนลด {discount_pct}% ที่ {partner}"
        min_tier = rng.choice(["FREE", "FREE", "PLUS", "PLUS", "PREMIUM"])
        items.append({
            "id": pid,
            "partner": partner,
            "title_th": title_th,
            "category": cat,
            "cost_points": cost_points,
            "discount_pct": discount_pct,
            "min_tier": min_tier,
            "segment": ["all"],
            "expires": "2026-12-31",
        })
    return items


# =============================================================================
# FAQ (~20)
# =============================================================================
FAQ_ITEMS: list[dict] = [
    {"id": "f-001", "question_th": "วิธีสมัครและยกเลิกแพ็กเกจ TrueID ทำอย่างไร",
     "answer_th": "สมัครได้ในแอป TrueID > เมนูแพ็กเกจ และยกเลิกได้ก่อนรอบบิลถัดไปทางช่องเดียวกัน",
     "tags": ["package", "billing"]},
    {"id": "f-002", "question_th": "ดูพร้อมกันกี่จอในแต่ละแพ็ก",
     "answer_th": "FREE ดูได้ 1 จอ, TrueID+ และ TrueID Premium ดูพร้อมกัน 2 จอ",
     "tags": ["package", "device"]},
    {"id": "f-003", "question_th": "ดูพรีเมียร์ลีกใน TrueID ต้องใช้แพ็กไหน",
     "answer_th": "ต้องเป็นแพ็ก TrueID Premium ขึ้นไปจึงจะรับชมการถ่ายทอดสดพรีเมียร์ลีกได้ครบทุกแมตช์",
     "tags": ["sports", "package", "premier_league"]},
    {"id": "f-004", "question_th": "ใช้คะแนน TrueID แลกของรางวัลอย่างไร",
     "answer_th": "เข้าเมนูสิทธิพิเศษในแอป เลือกของรางวัล แล้วกดแลก คะแนนจะถูกหักทันที",
     "tags": ["privileges", "points"]},
    {"id": "f-005", "question_th": "วิธีดาวน์โหลดดูออฟไลน์",
     "answer_th": "แตะปุ่มดาวน์โหลดในหน้ารายละเอียดเรื่อง รองรับเฉพาะแพ็ก TrueID+ ขึ้นไป",
     "tags": ["app", "offline"]},
    {"id": "f-006", "question_th": "เปิดซับไตเติลภาษาไทยและภาษาอังกฤษอย่างไร",
     "answer_th": "ระหว่างเล่นกดไอคอน CC แล้วเลือกภาษาที่ต้องการ ภาษามีให้เลือกตามรายการ",
     "tags": ["subtitle", "app"]},
    {"id": "f-007", "question_th": "ระบบ Parental Control ตั้งค่าอย่างไร",
     "answer_th": "เข้าเมนูบัญชี > ปกครอง เพื่อกำหนดเรตเนื้อหา และตั้งรหัสล็อกได้",
     "tags": ["kids", "parental"]},
    {"id": "f-008", "question_th": "ช่องทางชำระเงินมีอะไรบ้าง",
     "answer_th": "รองรับบัตรเครดิต, บัตรเดบิต, TrueMoney Wallet, และหัก True Move H ต่อรอบบิล",
     "tags": ["billing", "payment"]},
    {"id": "f-009", "question_th": "ดูจากทีวีบ้านได้หรือไม่",
     "answer_th": "รองรับ Smart TV (Android TV, Samsung, LG), Apple TV, Chromecast และ AirPlay",
     "tags": ["device", "tv"]},
    {"id": "f-010", "question_th": "ทดลองใช้ฟรีมีกี่วัน",
     "answer_th": "ลูกค้าใหม่ทดลองใช้ TrueID+ ฟรี 7 วันโดยไม่ต้องตัดบัตรครั้งแรก",
     "tags": ["trial", "package"]},
    {"id": "f-011", "question_th": "ฟุตบอลแชมเปียนส์ลีกอยู่แพ็กไหน",
     "answer_th": "การถ่ายทอดสดแชมเปียนส์ลีกอยู่ในแพ็ก TrueID Premium",
     "tags": ["sports", "champions_league", "package"]},
    {"id": "f-012", "question_th": "ไทยลีก 1 ดูได้ในแพ็กอะไร",
     "answer_th": "ไทยลีก 1 ครบทุกแมตช์รับชมได้บนแพ็ก TrueID+ ขึ้นไป",
     "tags": ["sports", "thai_league", "package"]},
    {"id": "f-013", "question_th": "ดูแบบ 4K ต้องเป็นแพ็กไหน",
     "answer_th": "คุณภาพระดับ 4K HDR ใช้ได้กับ TrueID Premium บนอุปกรณ์ที่รองรับ",
     "tags": ["quality", "package"]},
    {"id": "f-014", "question_th": "นโยบายคืนเงินเป็นอย่างไร",
     "answer_th": "หากชำระแล้วไม่พอใจติดต่อ Call Center ภายใน 7 วันเพื่อพิจารณาคืนเงินตามเงื่อนไข",
     "tags": ["billing", "refund"]},
    {"id": "f-015", "question_th": "เปลี่ยนแพ็กจาก TrueID+ ไป Premium ทันทีได้หรือไม่",
     "answer_th": "ทำได้ทันที โดยจะคิดส่วนต่างของรอบบิลปัจจุบันให้อัตโนมัติ",
     "tags": ["package", "upgrade"]},
    {"id": "f-016", "question_th": "ดูในต่างประเทศได้หรือไม่",
     "answer_th": "เนื้อหาบางส่วนรับชมได้นอกประเทศไทย คอนเทนต์ลิขสิทธิ์เฉพาะอาจถูกจำกัด",
     "tags": ["geo", "travel"]},
    {"id": "f-017", "question_th": "ใช้บัญชีเดียวกันในครอบครัวได้กี่คน",
     "answer_th": "สูงสุด 5 โปรไฟล์ต่อบัญชี และดูพร้อมกันตามจำนวนจอที่แพ็กกำหนด",
     "tags": ["account", "family"]},
    {"id": "f-018", "question_th": "เกมและ esports ดูได้ไหม",
     "answer_th": "TrueID มีคอนเทนต์ esports และไฮไลท์เกม รวมถึงรายการสด eFootball เฉพาะแพ็ก Premium",
     "tags": ["esports", "package"]},
    {"id": "f-019", "question_th": "Casting ขึ้นทีวีทำอย่างไร",
     "answer_th": "แตะปุ่ม Cast ในแอปแล้วเลือกอุปกรณ์รับสัญญาณ Chromecast / AirPlay",
     "tags": ["device", "tv"]},
    {"id": "f-020", "question_th": "ติดต่อทีมงานช่องทางไหน",
     "answer_th": "Live chat ในแอป, Call Center 1242 หรืออีเมล support@trueid.net 24 ชั่วโมง",
     "tags": ["support", "contact"]},
]


# =============================================================================
# Matches (~12). Kickoffs are anchored around REFERENCE_DATE = 2026-06-14.
# =============================================================================
def _matches() -> list[dict]:
    return [
        {"id": "m-001", "competition": "Premier League",
         "home_th": "แมนเชสเตอร์ ซิตี้", "away_th": "ลิเวอร์พูล",
         "home_en": "Manchester City", "away_en": "Liverpool",
         "kickoff": "2026-06-13T22:30:00+07:00", "channel": "TrueID Premium Sport 1",
         "min_package": "PREMIUM", "status": "scheduled",
         "head_to_head_th": "5 นัดหลังสุด ซิตี้ชนะ 2 เสมอ 2 แพ้ 1"},
        {"id": "m-002", "competition": "Premier League",
         "home_th": "ลิเวอร์พูล", "away_th": "อาร์เซนอล",
         "home_en": "Liverpool", "away_en": "Arsenal",
         "kickoff": "2026-06-14T21:30:00+07:00", "channel": "TrueID Premium Sport 1",
         "min_package": "PREMIUM", "status": "scheduled",
         "head_to_head_th": "5 นัดหลังสุด ลิเวอร์พูลชนะ 3 เสมอ 1 แพ้ 1"},
        {"id": "m-003", "competition": "La Liga",
         "home_th": "เรอัล มาดริด", "away_th": "บาร์เซโลนา",
         "home_en": "Real Madrid", "away_en": "Barcelona",
         "kickoff": "2026-06-15T02:00:00+07:00", "channel": "TrueID Premium Sport 2",
         "min_package": "PREMIUM", "status": "scheduled",
         "head_to_head_th": "เอลกลาซิโก้ 5 นัดล่าสุด เรอัลชนะ 2 เสมอ 1 แพ้ 2"},
        {"id": "m-004", "competition": "Premier League",
         "home_th": "แมนเชสเตอร์ ยูไนเต็ด", "away_th": "เชลซี",
         "home_en": "Manchester United", "away_en": "Chelsea",
         "kickoff": "2026-06-14T19:30:00+07:00", "channel": "TrueID Premium Sport 1",
         "min_package": "PREMIUM", "status": "scheduled",
         "head_to_head_th": "5 นัดหลังสุด ยูไนเต็ดชนะ 2 เสมอ 1 แพ้ 2"},
        {"id": "m-005", "competition": "UEFA Champions League",
         "home_th": "บาเยิร์น มิวนิก", "away_th": "ปารีส แซงต์ แชร์กแมง",
         "home_en": "Bayern Munich", "away_en": "Paris Saint-Germain",
         "kickoff": "2026-06-16T02:00:00+07:00", "channel": "TrueID Premium Sport 2",
         "min_package": "PREMIUM", "status": "scheduled",
         "head_to_head_th": "พบกัน 4 นัด บาเยิร์นชนะ 2 เสมอ 1 แพ้ 1"},
        {"id": "m-006", "competition": "Thai League 1",
         "home_th": "บีจี ปทุม ยูไนเต็ด", "away_th": "บุรีรัมย์ ยูไนเต็ด",
         "home_en": "BG Pathum United", "away_en": "Buriram United",
         "kickoff": "2026-06-14T18:00:00+07:00", "channel": "TrueID Premium Sport 3",
         "min_package": "PLUS", "status": "scheduled",
         "head_to_head_th": "5 นัดหลังสุด บุรีรัมย์ชนะ 3 เสมอ 1 แพ้ 1"},
        {"id": "m-007", "competition": "Premier League",
         "home_th": "ท็อตแนม", "away_th": "นิวคาสเซิล",
         "home_en": "Tottenham", "away_en": "Newcastle",
         "kickoff": "2026-06-14T23:00:00+07:00", "channel": "TrueID Premium Sport 1",
         "min_package": "PREMIUM", "status": "scheduled",
         "head_to_head_th": "5 นัดหลังสุด ท็อตแนมชนะ 2 เสมอ 2 แพ้ 1"},
        {"id": "m-008", "competition": "Premier League",
         "home_th": "แอสตัน วิลล่า", "away_th": "ไบรท์ตัน",
         "home_en": "Aston Villa", "away_en": "Brighton",
         "kickoff": "2026-06-14T01:00:00+07:00", "channel": "TrueID Premium Sport 1",
         "min_package": "PREMIUM", "status": "scheduled",
         "head_to_head_th": "5 นัดหลังสุด วิลล่าชนะ 3 เสมอ 0 แพ้ 2"},
        {"id": "m-009", "competition": "Bundesliga",
         "home_th": "บาเยิร์น มิวนิก", "away_th": "ดอร์ทมุนด์",
         "home_en": "Bayern Munich", "away_en": "Dortmund",
         "kickoff": "2026-06-15T01:30:00+07:00", "channel": "TrueID Premium Sport 2",
         "min_package": "PREMIUM", "status": "scheduled",
         "head_to_head_th": "เดอร์ คลาสซิเกอร์ 5 นัดล่าสุด บาเยิร์นชนะ 4 เสมอ 1"},
        {"id": "m-010", "competition": "Serie A",
         "home_th": "อินเตอร์ มิลาน", "away_th": "เอซี มิลาน",
         "home_en": "Inter Milan", "away_en": "AC Milan",
         "kickoff": "2026-06-15T00:45:00+07:00", "channel": "TrueID Premium Sport 2",
         "min_package": "PREMIUM", "status": "scheduled",
         "head_to_head_th": "ดาร์บี้มิลาน 5 นัดล่าสุด อินเตอร์ชนะ 3 เสมอ 1 แพ้ 1"},
        {"id": "m-011", "competition": "Premier League",
         "home_th": "เอฟเวอร์ตัน", "away_th": "วูล์ฟแฮมป์ตัน",
         "home_en": "Everton", "away_en": "Wolves",
         "kickoff": "2026-06-15T20:00:00+07:00", "channel": "TrueID Premium Sport 1",
         "min_package": "PREMIUM", "status": "scheduled",
         "head_to_head_th": "5 นัดหลังสุด เอฟเวอร์ตันชนะ 2 เสมอ 2 แพ้ 1"},
        {"id": "m-012", "competition": "UEFA Champions League",
         "home_th": "เรอัล มาดริด", "away_th": "ลิเวอร์พูล",
         "home_en": "Real Madrid", "away_en": "Liverpool",
         "kickoff": "2026-06-17T02:00:00+07:00", "channel": "TrueID Premium Sport 2",
         "min_package": "PREMIUM", "status": "scheduled",
         "head_to_head_th": "พบกัน 6 นัด เรอัลชนะ 3 เสมอ 1 แพ้ 2"},
    ]


# =============================================================================
# Users (~6) — mix of tiers so eval covers all entitlement outcomes.
# =============================================================================
def _users() -> list[dict]:
    return [
        {"user_id": "u_001", "current_package": "TrueID+", "tier": "PLUS",
         "points": 120, "segment": "returning"},
        {"user_id": "u_002", "current_package": "FREE", "tier": "FREE",
         "points": 20, "segment": "trial"},
        {"user_id": "u_003", "current_package": "TrueID Premium", "tier": "PREMIUM",
         "points": 500, "segment": "loyal"},
        {"user_id": "u_004", "current_package": "TrueID+", "tier": "PLUS",
         "points": 80, "segment": "returning"},
        {"user_id": "u_005", "current_package": "FREE", "tier": "FREE",
         "points": 0, "segment": "new"},
        {"user_id": "u_006", "current_package": "TrueID Premium", "tier": "PREMIUM",
         "points": 750, "segment": "loyal"},
    ]


# =============================================================================
# IO helpers
# =============================================================================
def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    rng = random.Random(SEED)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    catalog = _gen_catalog(rng)
    privileges = _gen_privileges(rng)
    matches = _matches()
    users = _users()

    _write_jsonl(DATA_DIR / "catalog.jsonl", catalog)
    _write_json(DATA_DIR / "packages.json", PACKAGES)
    _write_jsonl(DATA_DIR / "privileges.jsonl", privileges)
    _write_jsonl(DATA_DIR / "faq.jsonl", FAQ_ITEMS)
    _write_jsonl(DATA_DIR / "matches.jsonl", matches)
    _write_jsonl(DATA_DIR / "users.jsonl", users)

    print(
        f"data generation complete: "
        f"catalog={len(catalog)} privileges={len(privileges)} "
        f"faq={len(FAQ_ITEMS)} matches={len(matches)} users={len(users)}"
    )


if __name__ == "__main__":
    main()
