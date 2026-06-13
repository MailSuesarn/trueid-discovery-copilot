"""The fixed pipeline behind /chat (NOT a free-form agent loop).

classify -> hybrid retrieve -> deterministic tool(s) -> policy action -> LLM compose
(grounded JSON) -> validate. Emits one structured log per request
(request_id, intent, latency_ms, tokens, cost). See ARCHITECTURE.md §2.
"""
from __future__ import annotations

import logging
import time

from app.agent.guardrails import as_safe_context, clamp_input
from app.agent.intent import classify
from app.api.middleware import redact_pii
from app.api.schemas import ChatRequest, ChatResponse
from app.core.logging import log_event
from app.llm.gateway import compose, last_usage
from app.retrieval.hybrid import RetrievedDoc, get_retriever
from app.tools.privilege import decide_action, find_privileges

_log = logging.getLogger("orchestrator")


def _title_for(doc: RetrievedDoc) -> str:
    m = doc.meta
    return (
        m.get("title_th")
        or m.get("question_th")
        or (f"{m.get('home_th', '')} vs {m.get('away_th', '')}" if m.get("competition") else "")
        or m.get("partner")
        or doc.id
    )


def _synopsis_for(doc: RetrievedDoc) -> str:
    m = doc.meta
    return (
        m.get("synopsis_th")
        or m.get("answer_th")
        or m.get("head_to_head_th")
        or m.get("title_th")
        or ""
    )


def _top_doc_payload(docs: list[RetrievedDoc], k: int = 5) -> list[dict]:
    out: list[dict] = []
    for d in docs[:k]:
        out.append({
            "id": d.id,
            "title": _title_for(d),
            "synopsis": _synopsis_for(d),
            "min_package": d.meta.get("min_package"),
            "type": d.meta.get("type") or ("match" if d.meta.get("competition") else None),
        })
    return out


def _target_min_package(docs: list[RetrievedDoc], prefer_namespace: str | None = None) -> str | None:
    """Pick the first retrieved doc with a min_package. Optionally prefer match/catalog."""
    if prefer_namespace:
        for d in docs:
            if d.id.startswith(prefer_namespace) and d.meta.get("min_package"):
                return d.meta["min_package"]
    for d in docs:
        if d.meta.get("min_package"):
            return d.meta["min_package"]
    return None


def _build_tool_results_block(intent: str, policy: dict, target: str | None,
                              privileges: list[dict]) -> str:
    """Render the deterministic facts the LLM must reflect (not invent)."""
    lines = [f"intent: {intent}", f"policy_action: {policy['action']}"]
    if target:
        lines.append(f"target_min_package: {target}")
    if policy["upsell"].get("package"):
        lines.append(f"upsell_package: {policy['upsell']['package']}")
    if policy["upsell"].get("reason_th"):
        lines.append(f"upsell_reason_th: {policy['upsell']['reason_th']}")
    if privileges:
        lines.append(
            "eligible_privileges: " + ", ".join(
                f"{p['id']}({p.get('partner', '')})" for p in privileges[:3]
            )
        )
    return "\n".join(lines)


def handle_chat(req: ChatRequest) -> ChatResponse:
    t0 = time.perf_counter()
    safe_message = clamp_input(redact_pii(req.message))

    intent_info = classify(safe_message)
    intent = intent_info["intent"]

    retriever = get_retriever()
    retrieved = retriever.search(safe_message)

    privileges: list[dict] = []
    target_min_package: str | None = None
    if intent == "find_privilege":
        privileges = find_privileges(req.user_id, safe_message)
    elif intent == "live_schedule":
        target_min_package = _target_min_package(retrieved, prefer_namespace="match:")
    elif intent in {"find_content", "entitlement_check"}:
        target_min_package = _target_min_package(retrieved, prefer_namespace="catalog:")
    # recommend_package: target_min_package stays None — the policy upgrades by default.

    policy = decide_action(req.user_id, intent, {
        "target_min_package": target_min_package,
        "privileges": privileges,
    })

    top_docs = _top_doc_payload(retrieved)
    variables = {
        "user_message": safe_message,
        "retrieved_context": as_safe_context(retrieved[:5]),
        "tool_results": _build_tool_results_block(intent, policy, target_min_package, privileges),
        "top_docs": top_docs,
        "policy": policy,
        "intent": intent,
    }

    composed = compose("answer_compose", variables, ChatResponse)
    response = ChatResponse(**composed)

    usage = last_usage()
    log_event(
        _log, "chat",
        intent=intent,
        language=intent_info["language"],
        latency_ms=int((time.perf_counter() - t0) * 1000),
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        cost_usd=usage.get("cost_usd", 0.0),
        model=usage.get("model", ""),
        action=response.action,
    )
    return response
