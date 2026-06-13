import pytest


@pytest.mark.skip(reason="TODO(claude-code, Phase 7): each of the 5 intents returns a valid ChatResponse in mock mode")
def test_chat_all_intents(client):
    # for msg, expected_intent in CASES:
    #     r = client.post("/chat", json={"user_id": "u_001", "message": msg})
    #     assert r.status_code == 200
    #     body = r.json()
    #     assert body["action"] in {"play", "upgrade", "redeem", "none"}
    #     assert isinstance(body["citations"], list)
    ...
