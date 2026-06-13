"""The fixed pipeline behind /chat (NOT a free-form agent loop).

classify -> hybrid retrieve -> deterministic tool(s) -> policy action -> LLM compose
(grounded JSON) -> validate. Emits one structured log per request
(request_id, intent, latency_ms, tokens, cost). See ARCHITECTURE.md §2.
"""
from __future__ import annotations

from app.api.schemas import ChatRequest, ChatResponse


def handle_chat(req: ChatRequest) -> ChatResponse:
    raise NotImplementedError("Phase 5: implement the 6-step pipeline and return a validated ChatResponse")
