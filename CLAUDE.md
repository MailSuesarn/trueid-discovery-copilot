# CLAUDE.md — operating contract for this repo

You are implementing a take-home AI Engineer assessment. This file is loaded every
session. Read `PLAN.md` (what to build, in order) and `ARCHITECTURE.md` (how it fits
together) before writing code. Keep them in sync if you change the design.

## What this is
**TrueID Discovery & Monetization Copilot** — an entitlement-aware conversational
agent for TrueID (True Digital). It helps users find content (including live
sports), checks whether their package can play it, surfaces relevant privileges,
and ends with a single governed action (`play` / `upgrade` / `redeem` / `none`).
Backend only; the "UI" the grader sees is JSON responses, a metrics table, and
green pytest output inside a Colab notebook.

## THE #1 RULE (above everything)
The submission notebook must run **end-to-end on a fresh Google Colab CPU runtime
with only an OpenAI API key — and even with NO key**. If it errors, the score is
**0**, no resubmission. Therefore, for every decision ask: *"will this run in a
clean CPU Colab in under ~10 minutes, deterministically?"*
- Default code paths run on **CPU**. No GPU assumptions. No heavy model downloads.
- The system must degrade gracefully: `provider` LLM → `extractive` (no LLM) so it
  works with no key; dense retrieval → BM25-only if embeddings/key are absent.
- Tests use a **MockLLM and never touch the network**.
- Pin every dependency (already done in `requirements.txt`). Don't add heavy deps.

## Tech stack (don't deviate without reason)
Python 3.10+, FastAPI + Pydantic v2, OpenAI Python SDK (`openai>=2.41,<3`),
`rank-bm25` + `numpy`/`scikit-learn` for hybrid retrieval, `pyyaml`/`pydantic-settings`
for config, `tenacity` for retries, `pytest` + `ruff`. No agent framework — the
orchestration is explicit Python (see below). No database — synthetic data only.

## Architecture in one line
`/chat` → PII redact + request id → classify intent → hybrid retrieve (BM25+dense+RRF)
→ deterministic domain tool(s) → LLM composes a grounded answer + structured JSON
action → Pydantic validates → return. This is a **fixed pipeline, not a free-form
agent loop** (predictable = testable = safe). Details in `ARCHITECTURE.md`.

## OpenAI specifics (verified June 2026 — get these right)
- Default model `gpt-5.5`, cheap `gpt-5.4-mini`. **`gpt-5.5` is a reasoning model:**
  it REJECTS `temperature`/`top_p` and uses `max_completion_tokens` (chat) /
  `max_output_tokens` (responses). Steer with `reasoning_effort` + `verbosity`.
  Implement params **per model family** so we never throw a 400 (see ARCHITECTURE.md).
- Structured output: prefer the Responses API `client.responses.parse(..., text_format=Model)`
  with a Pydantic model; fall back to `client.chat.completions.parse(...)`.
- Embeddings: `text-embedding-3-large`, `dimensions=1024`. Cache catalog vectors to
  `data/index/embeddings.npz` and **commit the cache** so Colab ingest is offline.

## Conventions
- Config over constants: tunables live in `configs/app.yaml`, read via `app/core/config.py`.
  Env vars override config. Never hardcode keys, model names, thresholds, or paths.
- Every module has a docstring stating its single responsibility. Functions are typed.
- Structured JSON logging with a `request_id`; count tokens + cost per request.
- Keep functions small and pure where possible; the deterministic tools must be
  unit-testable without any LLM.
- Prompts are versioned files in `prompts/` — never inline prompt strings in code.
- Reuse the exam's Q2.1 Thai-ID regex as the real PII middleware (see ARCHITECTURE.md).

## How to run / verify (use these constantly)
```bash
make setup        # pip install -r requirements.txt  (installs this package editable)
make data         # generate synthetic data
make ingest       # build index + embedding cache
make test         # LLM_MODE=mock pytest   (must stay green, no network)
make eval         # prints the metrics table; --check enforces thresholds (CI gate)
make serve        # uvicorn on :8000 for manual poking
make lint         # ruff
```
A change isn't done until `make lint`, `make test`, and `make eval` all pass.

## Definition of done (the whole project)
1. `make data && make ingest && make test && make eval` all pass locally on CPU.
2. The FastAPI `/chat` endpoint returns the JSON contract (answer_th, citations,
   action, upsell), validated by Pydantic, for all 5 intents.
3. The eval harness reports Hit@3, MRR, action accuracy, groundedness, latency
   p50/p95, and cost/query, meeting the thresholds in `configs/app.yaml`.
4. `notebooks/exam.ipynb` runs top-to-bottom on a fresh CPU runtime: clones, installs,
   ingests, runs pytest, runs ~5 live `TestClient` queries, prints the metrics table,
   ends with the deployment/scaling/LLMOps markdown. Works WITH and WITHOUT a key.
5. `README.md` has the pitch, architecture, KPIs, and both run paths (Colab + Docker).
6. CI is green (lint → test → smoke eval → docker build).

## Working agreement
- Follow `PLAN.md` phase order. After each phase, run the verify commands and stop
  for a quick check-in if something is ambiguous — the human may spot-check between
  phases. Prefer a working vertical slice early over a perfect-but-unrunnable whole.
- Don't gold-plate. Simplicity that runs beats sophistication that risks the #1 rule.
- If you must choose between "more impressive" and "definitely runs," choose runs.
