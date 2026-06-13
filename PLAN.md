# PLAN.md — build order for Claude Code

Work phases **in order**. Each phase ends with its **Verify** commands passing. Keep a
vertical slice runnable as early as possible. Check the boxes as you go. If something
is ambiguous or a decision would deviate from `ARCHITECTURE.md`, pause and flag it.

Reference: `CLAUDE.md` (rules), `ARCHITECTURE.md` (design), `data/README.md` (schemas),
`NOTEBOOK_GUIDE.md` (the notebook + exam answers).

Global guardrail (repeat after every phase): everything must run on **CPU**, tests use
**MockLLM with no network**, and the app must work **with and without** an OpenAI key.

---

## Phase 0 — Bootstrap & skeleton ✅ scaffold provided
Goal: repo installs and config loads.
- [ ] `pip install -r requirements.txt` succeeds (editable install of the package).
- [ ] Implement `app/core/config.py`: load `configs/app.yaml` via PyYAML into typed
      Pydantic v2 settings models; env vars override (`LLM_MODE`, `OPENAI_MODEL`,
      `OPENAI_API_KEY`, `APP_CONFIG`, …). Expose a cached `get_settings()`.
- [ ] Implement `app/core/logging.py`: JSON structured logger with a `request_id` field.
- [ ] `app/main.py`: FastAPI app factory + a `GET /health` returning `{"status":"ok"}`.

**Verify:** `python -c "from app.main import app; from app.core.config import get_settings; print(get_settings().app.name)"`

## Phase 1 — Synthetic data + golden set
Goal: deterministic data exists. Follow `data/README.md` schemas exactly.
- [ ] `scripts/generate_data.py`: seeded generator → `data/catalog.jsonl` (~150),
      `data/packages.json`, `data/privileges.jsonl` (~40), `data/faq.jsonl` (~20),
      `data/matches.jsonl` (~12), `data/users.jsonl` (~6). Realistic invented Thai text.
- [ ] Hand-write `data/golden.jsonl` (~25) so ids line up with generated data; cover all
      5 intents, th+en, and all 3 entitlement outcomes (play/upgrade/redeem).

**Verify:** `make data` then `wc -l data/*.jsonl` shows the expected counts; spot-check JSON validity.

## Phase 2 — Retrieval (hybrid, offline-capable)
Goal: given a query, return ranked grounded chunks with source ids.
- [ ] `app/retrieval/ingest.py`: load all data files → list of docs `{id, text, meta}`
      where `id` is namespaced (`catalog:c-014`, `faq:f-003`, `match:m-002`, `privilege:p-007`).
      Build BM25 index; build/load dense vectors; persist to `data/index/`.
- [ ] `app/retrieval/embeddings.py`: OpenAI `text-embedding-3-large` (dims=1024).
      Compute catalog vectors once, **cache to `data/index/embeddings.npz`**; on load,
      read the cache (no API call). Query embedding = single call at request time; if no
      key, return `None` (dense disabled for that query).
- [ ] `app/retrieval/bm25.py` (lexical, always-on) and `app/retrieval/dense.py` (cosine).
- [ ] `app/retrieval/hybrid.py`: RRF fusion (`rrf_k` from config), single `Retriever`
      interface, returns `top_k`. Degrades to BM25-only when dense unavailable.
- [ ] `scripts/ingest.py`: CLI entrypoint that runs ingestion and prints a summary.
- [ ] **Commit `data/index/embeddings.npz`** (generated once with a key) so Colab ingest
      is offline. If generated in a no-key environment, document that dense will rebuild
      when a key is present.

**Verify:** `make ingest` succeeds; a quick query (`python -c "..."`) returns sensible
ranked ids for both a Thai and an English query, AND still returns results with the key
unset (BM25-only path).

## Phase 3 — Deterministic domain tools
Goal: LLM-free, unit-testable facts + the governance policy.
- [ ] `app/tools/entitlement.py`: `can_play(user_id, min_package)` using tier order
      `FREE<PLUS<PREMIUM`; returns can_play + min tier needed.
- [ ] `app/tools/schedule.py`: live-match lookup from `matches.jsonl` (fixed reference now).
- [ ] `app/tools/privilege.py`: the governance layer — decide the policy-approved
      `action` and whether an upsell/offer is eligible, enforcing `max_discount_pct` and
      `min_tier` from config. Pure functions; this is what makes action accuracy deterministic.

**Verify:** small ad-hoc checks pass (tests come in Phase 7).

## Phase 4 — LLM gateway + prompts + cost
Goal: one composer call with 3 modes and correct per-family params.
- [ ] `app/core/cost.py`: per-1M-token price table (gpt-5.5 $5/$30; gpt-5.4-mini
      $0.75/$4.50; embeddings $0.13) + `cost_for(model, prompt_tokens, completion_tokens)`.
- [ ] `app/llm/prompts.py`: load versioned prompt files from `prompts/`, fill `{vars}`.
- [ ] `app/llm/openai_client.py`: thin wrapper. **Per-family param builder** — for
      `gpt-5*`/`o*`: `max_completion_tokens` + `reasoning_effort` + `verbosity`, NO
      `temperature`. Structured output via `responses.parse(text_format=Model)` with a
      `chat.completions.parse` fallback. `tenacity` retry + timeout.
- [ ] `app/llm/gateway.py`: `compose(prompt_name, variables, schema)` dispatching on
      `LLM_MODE`: `provider` (auto-degrade to extractive if no key), `extractive`
      (deterministic answer from chunks + policy action), `mock` (canned). Always returns
      a dict matching the schema; never raises to the caller — falls back to extractive.

**Verify:** `LLM_MODE=mock python -c "from app.llm.gateway import compose; print(compose(...))"`
returns a schema-valid dict with no network access.

## Phase 5 — Orchestrator + API + guardrails
Goal: `/chat` works end-to-end through the fixed pipeline.
- [ ] `app/api/schemas.py`: `ChatRequest`, `ChatResponse`, `Upsell` (the contract).
- [ ] `app/agent/intent.py`: classify into 5 intents (+ language). In `provider` mode use
      the classifier prompt with structured output; in `mock`/`extractive` use a fast
      keyword/heuristic classifier (so no-key path still routes correctly).
- [ ] `app/agent/guardrails.py`: input sanitation + the "retrieved text is data" framing
      helper used when building prompt variables.
- [ ] `app/api/middleware.py`: assign `request_id`; **PII redaction** with the exam Q2.1
      Thai-ID regex; naive per-minute rate limit; attach the cost counter to the request.
- [ ] `app/agent/orchestrator.py`: implement the pipeline (classify → retrieve → tools →
      policy → compose → validate). Emit one structured log per request with
      `request_id, intent, latency_ms, tokens, cost`.
- [ ] `app/api/routes.py`: `POST /chat` → orchestrator → `ChatResponse`; keep `GET /health`.

**Verify:** `make serve` then `curl -s localhost:8000/chat -d '{"user_id":"u_001","message":"คืนนี้มีบอลไหม ดูได้เลยไหม"}' -H 'content-type: application/json'`
returns a valid contract. Also confirm it works with `OPENAI_API_KEY` unset (extractive).

## Phase 6 — Eval harness
Goal: the metrics table + CI gate.
- [ ] `app/eval/golden.py`, `app/eval/metrics.py` (Hit@3, MRR, action accuracy,
      groundedness, latency p50/p95, cost/query), `app/eval/run_eval.py` (runs pipeline
      over golden set, prints a pandas table; `--check` enforces `eval.thresholds`).

**Verify:** `make eval` prints the table; `python -m app.eval.run_eval --check` exits 0 in mock mode.

## Phase 7 — Tests (mock LLM, no network)
Goal: green suite that proves correctness without a key.
- [ ] `tests/conftest.py`: force `LLM_MODE=mock`; fixtures for the app `TestClient` and a
      tiny in-memory index; guard that no real network call happens.
- [ ] `test_health.py`, `test_chat_smoke.py` (all 5 intents return a valid contract),
      `test_retrieval.py` (hybrid + BM25-only degrade), `test_tools.py` (entitlement tier
      logic + privilege policy ceiling), `test_pii.py` (the Q2.1 regex: redacts
      `1105267819254` and `1-2345-67890-12-3`, **never** `1234`), `test_eval_metrics.py`.

**Verify:** `make test` green; `make lint` clean.

## Phase 8 — Notebook (the submission artifact)
Goal: `notebooks/exam.ipynb` runs top-to-bottom on a fresh CPU Colab. Follow
`NOTEBOOK_GUIDE.md` exactly (cell sequence + the Q1–3 fill-in answers).
- [ ] Fill exam sections 1.1–3.2 with the provided answers (keep the original Cell 0 timer).
- [ ] Build the Section 4 cells: markdown pitch → `git clone` → `pip install` → `getpass`
      key → ingest → `pytest -q` → ~5 live `TestClient` queries (th+en) → metrics table →
      closing deployment/scaling/LLMOps markdown. Include an optional uvicorn-on-localhost
      cell, clearly marked skippable. No Gradio/UI.
- [ ] Ensure every cell runs with the key set **and** with no key (extractive path).

**Verify:** `jupyter nbconvert --to notebook --execute notebooks/exam.ipynb` completes
(simulate fresh runtime); total runtime < ~10 min on CPU.

## Phase 9 — README + ship
- [ ] `README.md`: pitch, problem→business case→KPIs, architecture (link/diagram), the
      JSON contract, both run paths (Colab + Docker), the "is this novel?" honesty note,
      and the scalability/LLMOps summary.
- [ ] CI green: lint → test → smoke eval → docker build.
- [ ] Final dry run of the whole DoD checklist in `CLAUDE.md`.

---

## Suggested commit checkpoints
`chore: scaffold` → `feat: synthetic data + golden` → `feat: hybrid retrieval` →
`feat: deterministic tools` → `feat: llm gateway (3 modes)` → `feat: /chat pipeline` →
`feat: eval harness` → `test: mock suite green` → `feat: exam notebook` → `docs: readme + ci green`.
