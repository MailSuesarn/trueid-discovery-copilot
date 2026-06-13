"""Intent classification into the 5 supported intents (+ detected language).

provider mode -> classifier prompt with structured output; mock/extractive -> fast
keyword heuristic so the no-key path still routes correctly. The heuristic is also the
ground-truth fallback when the LLM returns an unknown label.
"""
from __future__ import annotations

from pydantic import BaseModel

from app.core.config import get_settings

INTENTS = ["find_content", "entitlement_check", "live_schedule", "find_privilege", "recommend_package"]


class IntentResult(BaseModel):
    intent: str
    language: str


# Strong cues (specific phrases) override weak cues (single keywords). Lowercased.
_STRONG = {
    "recommend_package": [
        "recommend a package", "recommend a plan", "which plan", "which package",
        "cheapest paid", "cheapest plan", "best package", "best plan", "what plan should",
        "what package should", "i'm new to trueid",
        "แนะนำแพ็ก", "ควรใช้แพ็ก", "เปลี่ยนแพ็ก", "อัปเกรดแพ็ก", "แนะนำแพ็กไหน",
    ],
    "entitlement_check": [
        "can i watch", "can my plan", "with my package", "with my plan", "is included in my",
        "ได้ไหม", "ได้มั้ย", "แพ็กของฉัน", "ของฉันดู",
    ],
    "find_privilege": [
        "สิทธิพิเศษ", "สิทธิ์", "แลก", "ส่วนลด", "ของรางวัล", "คะแนน", "แต้ม",
        "ตั๋วหนังราคา", "ส่วนลดร้าน", "ร้านกาแฟ", "คาเฟ่อเมซอน",
        "privilege", "discount", "redeem", "deal", "deals", "voucher", "points",
    ],
    "live_schedule": [
        "พรีเมียร์ลีก", "premier league", "champions league", "แชมเปียนส์",
        "ลาลีกา", "la liga", "บุนเดสลีกา", "bundesliga", "เซเรียอา", "serie a", "ไทยลีก",
        "matches tonight", "match tonight", "kickoff", "ถ่ายทอดสด", "ช่องไหน", "ช่องอะไร",
        "เตะกี่โมง", "เตะกับ", "เตะวัน", " vs ", "ปะทะ",
    ],
}
_WEAK = {
    "live_schedule": ["live", "match", "matches", "kickoff", "ฟุตบอล", "บอล", "เตะ", "พบ", "เจอ"],
    "find_privilege": ["coffee", "shopping", "café", "cafe", "ช้อป"],
    "find_content": ["recommend", "watch", "want", "ดู", "อยากดู", "อนิเมะ", "ซีรีส์", "หนัง", "ภาพยนตร์", "การ์ตูน"],
}
_PRIORITY = ["recommend_package", "entitlement_check", "find_privilege", "live_schedule", "find_content"]


def _detect_language(text: str) -> str:
    thai = sum(1 for c in text if "฀" <= c <= "๿")
    ascii_alpha = sum(1 for c in text if c.isascii() and c.isalpha())
    return "th" if thai >= max(1, ascii_alpha // 2) else "en"


def _count(cues: dict[str, list[str]], text: str) -> dict[str, int]:
    return {intent: sum(1 for c in clist if c in text) for intent, clist in cues.items()}


def heuristic_classify(message: str) -> dict:
    """Strong cues > weak cues > default find_content. Priority list breaks ties."""
    text = " " + message.lower() + " "  # pad so " vs " etc. match at the edges

    strong = _count(_STRONG, text)
    if any(v > 0 for v in strong.values()):
        top = max(strong.values())
        winners = [k for k, v in strong.items() if v == top]
        for k in _PRIORITY:
            if k in winners:
                return {"intent": k, "language": _detect_language(message)}

    weak = _count(_WEAK, text)
    if any(v > 0 for v in weak.values()):
        top = max(weak.values())
        winners = [k for k, v in weak.items() if v == top]
        for k in _PRIORITY:
            if k in winners:
                return {"intent": k, "language": _detect_language(message)}

    return {"intent": "find_content", "language": _detect_language(message)}


def _provider_classify(message: str) -> dict:
    from app.llm.openai_client import structured_complete
    from app.llm.prompts import render

    cfg = get_settings().llm
    template = render("intent_classifier", user_message=message)
    # Role framing lives in prompts/intent_classifier.v*.md — no inline prompt strings in code.
    messages = [{"role": "user", "content": template}]
    try:
        parsed, _usage = structured_complete(cfg.model_cheap, messages, IntentResult)
        data = parsed.model_dump()
        if data.get("intent") in INTENTS and data.get("language") in {"th", "en"}:
            return data
    except Exception:
        pass
    return heuristic_classify(message)


def classify(message: str) -> dict:
    """Return {"intent": <one of INTENTS>, "language": "th"|"en"}."""
    mode = get_settings().effective_mode
    if mode == "provider":
        return _provider_classify(message)
    return heuristic_classify(message)
