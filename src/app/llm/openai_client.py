"""Thin OpenAI wrapper with PER-FAMILY parameter handling + structured output + retries.

CRITICAL (verified June 2026): gpt-5.x / o* are REASONING models — do NOT send
`temperature`/`top_p`; use `max_completion_tokens` (chat) / `max_output_tokens` (responses);
steer with `reasoning_effort` + `verbosity`. Structured output via responses.parse(text_format=Model)
with a chat.completions.parse fallback. Wrap in tenacity retry + timeout.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings


def is_reasoning_model(model: str) -> bool:
    return model.startswith(("gpt-5", "o1", "o3", "o4"))


def build_responses_params(model: str, max_output_tokens: int,
                           reasoning_effort: str, verbosity: str) -> dict:
    """Kwargs for client.responses.parse for the given model family."""
    params: dict[str, Any] = {"model": model, "max_output_tokens": max_output_tokens}
    if is_reasoning_model(model):
        params["reasoning"] = {"effort": reasoning_effort}
        params["text"] = {"verbosity": verbosity}
    else:
        params["temperature"] = 0.2
    return params


def build_chat_params(model: str, max_output_tokens: int,
                      reasoning_effort: str, verbosity: str) -> dict:
    """Kwargs for client.chat.completions.parse (fallback) for the given model family."""
    params: dict[str, Any] = {"model": model}
    if is_reasoning_model(model):
        params["max_completion_tokens"] = max_output_tokens
        params["reasoning_effort"] = reasoning_effort
        params["verbosity"] = verbosity
    else:
        params["max_tokens"] = max_output_tokens
        params["temperature"] = 0.2
    return params


def _client():
    """Lazily import the SDK so module load does not require it."""
    from openai import OpenAI

    cfg = get_settings().llm
    return OpenAI(timeout=cfg.request_timeout_s)


def _extract_usage(resp) -> dict:
    """Best-effort token extraction across Responses (input/output_tokens) and Chat (prompt/completion_tokens)."""
    u = getattr(resp, "usage", None)
    if u is None:
        return {"prompt_tokens": 0, "completion_tokens": 0}
    return {
        "prompt_tokens": int(getattr(u, "input_tokens", 0) or getattr(u, "prompt_tokens", 0) or 0),
        "completion_tokens": int(getattr(u, "output_tokens", 0) or getattr(u, "completion_tokens", 0) or 0),
    }


def structured_complete(model: str, messages: list[dict], schema: type[BaseModel]) -> tuple[BaseModel, dict]:
    """Call OpenAI and return (parsed_schema_instance, usage_dict).

    Tries `responses.parse` first, falls back to `chat.completions.parse`. Wraps the whole
    call in tenacity retries; the gateway catches the final exception and degrades to extractive.
    """
    cfg = get_settings().llm

    @retry(stop=stop_after_attempt(cfg.max_retries + 1),
           wait=wait_exponential(multiplier=0.5, min=0.5, max=4), reraise=True)
    def _call() -> tuple[BaseModel, dict]:
        client = _client()
        try:
            params = build_responses_params(model, cfg.max_output_tokens,
                                            cfg.reasoning_effort, cfg.verbosity)
            resp = client.responses.parse(
                input=messages,
                text_format=schema,
                **params,
            )
            parsed = getattr(resp, "output_parsed", None)
            if parsed is not None:
                return parsed, _extract_usage(resp)
        except Exception:
            # Fall through to chat.completions.parse below.
            pass

        chat_params = build_chat_params(model, cfg.max_output_tokens,
                                        cfg.reasoning_effort, cfg.verbosity)
        chat = client.chat.completions.parse(
            messages=messages,
            response_format=schema,
            **chat_params,
        )
        return chat.choices[0].message.parsed, _extract_usage(chat)

    return _call()
