"""End-to-end /chat smoke tests — each intent returns a valid ChatResponse contract."""
from __future__ import annotations

CASES = [
    ("u_001", "อยากดูซีรีส์เกาหลีแนวสืบสวน เบาๆ ก่อนนอน", "find_content"),
    ("u_001", "แพ็กของฉันดู Liverpool vs Arsenal ได้ไหม", "entitlement_check"),
    ("u_001", "คืนนี้มีบอลพรีเมียร์ลีกไหม ดูได้เลยหรือเปล่า", "live_schedule"),
    ("u_002", "มีสิทธิพิเศษร้านกาแฟใกล้ฉันไหม", "find_privilege"),
    ("u_002", "ครอบครัวมี 4 คนอยากดูพร้อมกัน แนะนำแพ็กไหน", "recommend_package"),
]
VALID_ACTIONS = {"play", "upgrade", "redeem", "none"}


def test_chat_all_intents(client):
    for user_id, msg, _intent in CASES:
        r = client.post("/chat", json={"user_id": user_id, "message": msg})
        assert r.status_code == 200, msg
        body = r.json()
        assert body["action"] in VALID_ACTIONS
        assert isinstance(body["citations"], list)
        assert isinstance(body["answer_th"], str) and body["answer_th"].strip()
        # upsell shape is always present, even when null inside.
        assert "package" in body["upsell"] and "reason_th" in body["upsell"]


def test_chat_response_has_request_id_header(client):
    r = client.post("/chat", json={"user_id": "u_001", "message": "อยากดูหนัง"})
    assert r.status_code == 200
    assert r.headers.get("x-request-id")
