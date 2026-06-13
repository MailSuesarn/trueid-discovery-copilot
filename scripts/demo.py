"""Quick manual demo: fire a handful of representative queries at /chat and pretty-print
the JSON contract. Uses the in-process TestClient (no port, no server to start).

Run:  python scripts/demo.py
The mode is whatever the config resolves to: with a key in .env -> provider (real LLM);
with no key -> extractive (offline). Each line's structured log shows intent/latency/cost.
"""
from __future__ import annotations

import json
import sys

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

# (user_id, message) — covers all 5 intents, both languages, and all 3 entitlement outcomes.
# u_001=PLUS, u_002=FREE, u_003=PREMIUM (see data/users.jsonl).
QUERIES: list[tuple[str, str]] = [
    ("u_001", "อยากดูซีรีส์เกาหลีแนวสืบสวน เบาๆ ก่อนนอน"),          # find_content   -> play
    ("u_001", "คืนนี้มีบอลพรีเมียร์ลีกไหม ดูได้เลยหรือเปล่า"),       # live_schedule  -> upgrade
    ("u_003", "แพ็กของฉันดู Liverpool vs Arsenal ได้ไหม"),          # entitlement    -> play
    ("u_002", "มีสิทธิพิเศษร้านกาแฟใกล้ฉันไหม"),                     # find_privilege -> redeem
    ("u_002", "ครอบครัวมี 4 คนอยากดูพร้อมกัน แนะนำแพ็กไหน"),        # recommend_pkg  -> upgrade
    ("u_001", "recommend a package if I mainly watch live football"),  # en, recommend -> upgrade
]


def main() -> None:
    settings = get_settings()
    print(f"=== TrueID Copilot demo | mode={settings.effective_mode} "
          f"| key={'yes' if settings.has_openai_key else 'no'} ===\n")

    client = TestClient(app)
    for user_id, message in QUERIES:
        resp = client.post("/chat", json={"user_id": user_id, "message": message})
        if resp.status_code != 200:
            print(f"[{user_id}] {message}\n  ERROR {resp.status_code}: {resp.text}\n")
            continue
        body = resp.json()
        print(f"[{user_id}] {message}")
        print(json.dumps(body, ensure_ascii=False, indent=2))
        print()


if __name__ == "__main__":
    sys.exit(main())
