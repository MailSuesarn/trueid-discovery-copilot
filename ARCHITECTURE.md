# ARCHITECTURE.md

## 1. Concept & business framing
**TrueID Discovery & Monetization Copilot** — an entitlement-aware conversational
layer over TrueID's content, packages, and privileges. Unlike a generic RAG chatbot,
**every answer knows what the user's package can actually play, and ends with one
honest, governed action** (`play` / `upgrade` / `redeem` / `none`). It complements
True's existing customer-care assistant (Mari) by owning the *discovery → monetization*
moment instead of support.

Why it scores on the rubric:
- **Business impact (35):** sits on the conversion funnel — reduces search
  abandonment, lifts trial→paid and privilege redemption. The action + governed
  upsell is the revenue surface. KPIs in `README.md`.
- **Creativity (20):** entitlement-aware answers + a *governed* next-best-action
  (policy-bounded, not a dark pattern) + a **live-sports flagship** intent (Premier
  League is TrueID's real moat vs global streamers).
- **Code quality (25):** modular `src/`, typed, Pydantic contracts, versioned prompts,
  mock-based tests, CI, Docker.
- **AI technique & scalability (20):** hybrid retrieval (BM25+dense+RRF), tool-calling
  + strict structured output, eval-driven LLMOps, stateless API with documented
  Qdrant/Redis scale path + model router.

## 2. Request flow (the fixed pipeline)
```
POST /chat {user_id, message}
   │
   ▼  app/api/middleware.py
[ request_id assigned ] → [ PII redaction (Thai-ID regex, reuses exam Q2.1) ] → [ rate limit ]
   │
   ▼  app/agent/orchestrator.py   (explicit pipeline — NOT a free-form agent loop)
   1. classify intent            app/agent/intent.py        → one of 5 intents (+ language)
   2. hybrid retrieve            app/retrieval/hybrid.py     → top_k grounded chunks (+ source ids)
   3. run deterministic tool(s)  app/tools/*                 → entitlement / schedule / privilege facts
   4. policy: decide action      app/tools/privilege.py      → governed action + eligible offer (code, not LLM)
   5. compose grounded answer    app/llm/gateway.py          → JSON via structured output
   6. validate                   app/api/schemas.py          → Pydantic ChatResponse
   │
   ▼
ChatResponse {answer_th, citations, action, upsell}   + structured log {request_id, intent, latency_ms, tokens, cost}
```
The pipeline is deterministic in shape; only step 5 calls the LLM, and even that has
a no-LLM fallback. This is what makes it testable and safe for the #1 rule.

## 3. The response contract (central)
`app/api/schemas.py` (Pydantic v2). This is also the LLM's structured-output schema.
```python
class Upsell(BaseModel):
    package: str | None = None
    reason_th: str | None = None

class ChatResponse(BaseModel):
    answer_th: str
    citations: list[str] = []          # source ids actually used, e.g. "catalog:c-014"
    action: Literal["play", "upgrade", "redeem", "none"]
    upsell: Upsell = Upsell()

class ChatRequest(BaseModel):
    user_id: str
    message: str
```
`action` is set from the **deterministic tool/policy result**, not invented by the
LLM — that is why action accuracy can be an exact-match metric.

## 4. Retrieval (hybrid, offline-capable)
`app/retrieval/`:
- `ingest.py` — load `data/*.jsonl`, build searchable docs (one record = one doc with
  an `id` like `catalog:c-014`, `faq:f-003`, `match:m-002`, `privilege:p-007`), build
  the BM25 index, compute/load dense vectors, persist to `data/index/`.
- `bm25.py` — lexical search (rank-bm25). Pure Python, **always available, offline**.
  This is the floor that guarantees retrieval works with no key.
- `embeddings.py` — OpenAI `text-embedding-3-large` (dims=1024). **Catalog vectors are
  cached to `data/index/embeddings.npz` and committed**, so ingest in Colab loads from
  disk (no embedding API calls, offline, instant). Only the *query* is embedded at
  request time (1 cheap call). If no key → skip dense for that query.
- `dense.py` — cosine similarity over cached vectors (numpy / sklearn).
- `hybrid.py` — **Reciprocal Rank Fusion** of BM25 + dense candidate lists
  (`score = Σ 1/(rrf_k + rank)`), returns `top_k`. If dense is unavailable, returns
  BM25-only results. Exposes a single `Retriever` interface so the backend can be
  swapped for Qdrant later without touching the orchestrator.

## 5. Deterministic domain tools
`app/tools/` — pure, LLM-free, unit-tested:
- `entitlement.py` — given `user_id` + an item's `min_package`, decide if the user's
  tier can play it (`tier order: FREE < PLUS < PREMIUM`). Returns can_play + the
  minimum tier needed.
- `schedule.py` — look up live matches (from `matches.jsonl`) for the `live_schedule`
  intent: kickoff, channel, required package. Uses a fixed reference "now" (no real
  clock) for reproducibility.
- `privilege.py` — the **governance layer**. Given the user + context, decide the
  policy-approved action and whether an upsell/offer is eligible, enforcing
  `monetization.max_discount_pct` and `min_tier`. Returns the action + offer that the
  composer must faithfully reflect. All limits enforced in code, never by the LLM.

## 6. LLM gateway (3 modes + per-family params)
`app/llm/gateway.py` exposes one function the orchestrator calls, e.g.
`compose(prompt_name, variables, schema) -> dict`. Mode from `configs/app.yaml`:
- **`provider`** — call OpenAI. Auto-degrades to `extractive` if `OPENAI_API_KEY`
  is missing (so a grader with no key still gets a real, runnable answer).
- **`extractive`** — NO LLM. Deterministically build `answer_th` from the top
  retrieved chunks + tool facts, and take `action` straight from the policy result.
  Guarantees end-to-end run with zero key/network.
- **`mock`** — canned deterministic outputs for tests; never hits the network.

**OpenAI parameter handling (verified June 2026 — implement carefully):**
- `gpt-5.5` / `gpt-5.4*` are **reasoning models**: do NOT send `temperature` or
  `top_p`; use `max_completion_tokens` (Chat Completions) / `max_output_tokens`
  (Responses API); steer with `reasoning_effort` (`low` default) and `verbosity`
  (`low` default for concise Thai). Build params **per family** so legacy chat models
  (if ever configured) still get `temperature`/`max_tokens`.
- Structured output: use `client.responses.parse(model=..., input=..., text_format=PydanticModel)`
  → `resp.output_parsed`; fallback `client.chat.completions.parse(...)`. This gives
  schema-valid JSON without brittle string parsing.
- Wrap calls in `tenacity` retry (`max_retries`, exponential backoff) + `request_timeout_s`.
  On final failure, fall back to `extractive` rather than 500 — the user always gets an answer.
- `app/core/cost.py` holds the per-1M-token price table (gpt-5.5 $5/$30; gpt-5.4-mini
  $0.75/$4.50; embeddings $0.13) and computes cost per request from token usage.

`app/llm/prompts.py` loads versioned prompt files from `prompts/` and fills `{vars}`.

## 7. Guardrails
`app/agent/guardrails.py`:
- **Prompt-injection hardening:** retrieved text + tool outputs are inserted inside
  `<context>`/`<tool_results>` blocks; the system prompt instructs the model to treat
  them as data and ignore embedded instructions. (Defense, not a guarantee — stated honestly.)
- **PII:** `app/api/middleware.py` redacts Thai national IDs on input using the exam
  Q2.1 regex `(?<!\d)\d-?\d{4}-?\d{5}-?\d{2}-?\d(?!\d)` → `<REDACTED>`. Nice narrative:
  a tiny exam question becomes a production middleware.
- **Input limits + naive rate limiting** from config.

## 8. Eval & LLMOps
`app/eval/`:
- `golden.py` — load `data/golden.jsonl`.
- `metrics.py` — **Hit@3** & **MRR** (retrieval: did `relevant_ids` appear?),
  **action accuracy** (exact match on `action`), **groundedness** (fraction of
  returned citations that are real source ids that were actually retrieved),
  **latency p50/p95**, **cost/query**.
- `run_eval.py` — run the pipeline (in `mock` or `provider` mode) over the golden set,
  print a pandas table; `--check` exits non-zero if below `eval.thresholds` (the CI
  quality gate). This is the LLMOps story made real: a regression fails the build.

Other LLMOps embedded in code (not just prose): versioned prompts, structured logging
+ request id + token/cost counter, retries/timeout/fallback in the gateway, the model
router (cheap model for simple intents), and the eval gate in CI.

## 9. Scalability story (for README + closing notebook markdown)
- **Stateless API** → horizontal scaling behind a load balancer; no session state in process.
- **Swappable vector store**: the `Retriever` interface lets the in-memory index be
  replaced by **Qdrant** (wired in `docker-compose.yml`) with no orchestrator changes.
- **Semantic cache** (Redis, in compose) for hot queries → lower latency + cost.
- **Model router**: simple/deterministic intents → `gpt-5.4-mini`; complex → `gpt-5.5`.
- **CI quality gate**: smoke eval must pass before deploy.
- **Cost control**: low `reasoning_effort`/`verbosity`, embedding cache, model routing,
  per-request cost accounting for observability.

## 10. How it runs in Colab (no Docker there)
Colab is one temporary Linux box; the API and the client (the notebook cells) live in
the same box. We call the app **in-process via FastAPI `TestClient`** (zero port risk),
with an optional cell that spins real `uvicorn` on localhost to show HTTP. Docker is the
*production* path (proven by CI building the image), explicitly **not** run in Colab.
See `NOTEBOOK_GUIDE.md`.
