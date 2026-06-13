"""LLM gateway: ONE entrypoint the orchestrator calls, dispatching on LLM_MODE.

modes: provider (OpenAI; auto-degrades to extractive if no key) | extractive (NO LLM,
deterministic answer from retrieved chunks + policy action) | mock (canned, for tests).
ALWAYS returns a dict matching the schema; never raises to the caller (falls back to
extractive on provider failure). See ARCHITECTURE.md §6.

`compose` expects these variables (the orchestrator builds them):
  user_message       : str   — original user message (PII redacted)
  retrieved_context  : str   — formatted <context> block (data, not instructions)
  tool_results       : str   — formatted <tool_results> block with policy action
  top_docs           : list  — [{"id","title","synopsis"}] used for extractive composition
  policy             : dict  — {"action","upsell":{...}} from decide_action (authoritative)
  intent             : str   — classified intent
"""
from __future__ import annotations

from pydantic import BaseModel

from app.core.config import get_settings
from app.core.cost import cost_for
from app.llm.prompts import render

# Per-request cost counter populated by the gateway, read by the orchestrator log.
_last_usage: dict = {"prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "model": ""}


def last_usage() -> dict:
    return dict(_last_usage)


def _reset_usage() -> None:
    _last_usage.update({"prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "model": ""})


def _pick_model(intent: str) -> str:
    cfg = get_settings().llm
    if cfg.router.enabled and intent in cfg.router.cheap_intents:
        return cfg.model_cheap
    return cfg.model


def _extractive_answer(variables: dict) -> dict:
    """Deterministic Thai answer built from the policy + the top retrieved doc."""
    policy = variables.get("policy") or {"action": "none", "upsell": {"package": None, "reason_th": None}}
    docs = variables.get("top_docs") or []
    intent = variables.get("intent", "")

    citations = [d["id"] for d in docs[:3]]
    if not docs:
        return {
            "answer_th": "ขออภัย ไม่พบข้อมูลที่ตรงกับคำถามในคลังคอนเทนต์ปัจจุบัน",
            "citations": [],
            "action": policy["action"],
            "upsell": policy["upsell"],
        }

    top = docs[0]
    title = top.get("title") or top.get("id")
    synopsis = top.get("synopsis", "").strip()

    action = policy["action"]
    upsell = policy["upsell"]

    if action == "play":
        body = f"แนะนำ {title} — {synopsis} แพ็กของคุณรับชมได้ทันที"
    elif action == "upgrade":
        pkg = upsell.get("package") or "แพ็กที่สูงกว่า"
        reason = upsell.get("reason_th") or "เพื่อปลดล็อกการรับชม"
        if intent == "live_schedule":
            body = f"การถ่ายทอดสดอยู่ในช่อง {title} — ต้องอัปเกรดเป็น {pkg} {reason}"
        elif intent == "recommend_package":
            body = f"แนะนำอัปเกรดเป็น {pkg} — {reason}"
        else:
            body = f"รายการ {title} ต้องใช้แพ็ก {pkg} ขึ้นไป — {reason}"
    elif action == "redeem":
        reason = upsell.get("reason_th") or f"แลกสิทธิ์ที่ {title}"
        body = reason
    else:
        body = f"พบรายการ {title} ที่อาจสนใจ — {synopsis}"

    return {
        "answer_th": body.strip(),
        "citations": citations,
        "action": action,
        "upsell": upsell,
    }


def _mock_answer(variables: dict) -> dict:
    """Canned deterministic output for tests — never touches the network."""
    extractive = _extractive_answer(variables)
    extractive["answer_th"] = "[mock] " + extractive["answer_th"]
    return extractive


def _provider_answer(prompt_name: str, variables: dict, schema: type[BaseModel]) -> dict:
    """Call OpenAI for the answer_th + citations; policy still owns action/upsell."""
    from app.llm.openai_client import structured_complete

    model = _pick_model(variables.get("intent", ""))
    template = render(
        prompt_name,
        user_message=variables.get("user_message", ""),
        retrieved_context=variables.get("retrieved_context", ""),
        tool_results=variables.get("tool_results", ""),
    )
    # The full role framing + grounding/governance rules live in the versioned prompt file
    # (prompts/answer_compose.v*.md) — no inline prompt strings in code. Send it as the sole message.
    messages = [{"role": "user", "content": template}]
    try:
        parsed, usage = structured_complete(model, messages, schema)
        data = parsed.model_dump()
    except Exception:
        # Any provider failure → extractive (the user always gets an answer).
        return _extractive_answer(variables)

    # Policy owns action + upsell. The LLM only contributes the prose + citations.
    policy = variables.get("policy") or {"action": "none", "upsell": {"package": None, "reason_th": None}}
    data["action"] = policy["action"]
    data["upsell"] = policy["upsell"]

    # Discard hallucinated citations — only ids that were actually retrieved are valid.
    retrieved_ids = {d["id"] for d in (variables.get("top_docs") or [])}
    data["citations"] = [c for c in (data.get("citations") or []) if c in retrieved_ids]
    if not data["citations"]:
        data["citations"] = [d["id"] for d in (variables.get("top_docs") or [])[:3]]

    pt, ct = usage["prompt_tokens"], usage["completion_tokens"]
    _last_usage.update({
        "prompt_tokens": pt, "completion_tokens": ct,
        "cost_usd": cost_for(model, pt, ct), "model": model,
    })
    return data


def compose(prompt_name: str, variables: dict, schema: type[BaseModel]) -> dict:
    """Produce a schema-valid dict (answer_th, citations, action, upsell)."""
    _reset_usage()
    mode = get_settings().effective_mode
    if mode == "mock":
        return _mock_answer(variables)
    if mode == "extractive":
        return _extractive_answer(variables)
    return _provider_answer(prompt_name, variables, schema)
