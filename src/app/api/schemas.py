"""Pydantic contracts for /chat. `ChatResponse` is ALSO the LLM structured-output schema."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Action = Literal["play", "upgrade", "redeem", "none"]


class ChatRequest(BaseModel):
    user_id: str
    message: str


class Upsell(BaseModel):
    package: str | None = None
    reason_th: str | None = None


class ChatResponse(BaseModel):
    answer_th: str
    citations: list[str] = Field(default_factory=list)
    action: Action
    upsell: Upsell = Field(default_factory=Upsell)
