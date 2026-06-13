"""HTTP routes: GET /health, POST /chat."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    # Lazy import: the app imports cleanly while the orchestrator is still a stub.
    from app.agent.orchestrator import handle_chat

    return handle_chat(req)
