# TrueID Discovery & Monetization Copilot

> An **entitlement-aware** conversational copilot for TrueID. It helps a user find
> something to watch — including **live sports** — tells them whether *their* package can
> actually play it, surfaces relevant privileges, and ends with **one honest, governed
> action** (`play` / `upgrade` / `redeem`). Built for the True Digital AI Engineer
> assessment as a production-shaped, eval-driven system.

It complements True's existing care assistant **Mari** (which owns support) by owning the
**discovery → monetization** moment — the part of the funnel that actually moves revenue.

---

## The problem & the business case

TrueID is a broad media-lifestyle platform: watch, listen, read, live TV/sports, games,
privileges, commerce. That breadth creates **discovery friction** — users abandon search,
miss content their package already includes, and never see the upgrade or privilege that
fits them. Classic search + recommendation rails don't *converse*, don't reason about a
user's **entitlement**, and don't close with an action.

This copilot turns a natural-language request into a grounded answer **plus a governed
next step**, on the conversion funnel itself.

### Target KPIs (illustrative, the way they'd be tracked)
- **Search/discovery abandonment** ↓ (fewer dead-end searches → sessions that resolve)
- **Trial → paid conversion** ↑ (entitlement-aware upgrade prompts at the moment of intent)
- **Privilege redemption** ↑ among prompted users (drives partner + retention value)
- **Play-start rate** ↑ from conversational discovery vs static rails

The upgrade prompt is a **governed next-best-action**: it only appears when a deterministic
policy says the user is eligible, and the discount is capped *in code*. Monetization without
dark patterns — and, because it's deterministic, it's **measurable to the exact action**.

---

## What it does (5 intents)
1. **find_content** — "อยากดูซีรีส์เกาหลีแนวสืบสวน เบาๆ ก่อนนอน"
2. **entitlement_check** — "แพ็กของฉันดู Liverpool vs Arsenal ได้ไหม"
3. **live_schedule** — "คืนนี้มีบอลพรีเมียร์ลีกไหม ดูได้เลยหรือเปล่า" *(flagship — live sports is TrueID's real moat)*
4. **find_privilege** — "มีสิทธิพิเศษร้านกาแฟใกล้ฉันไหม"
5. **recommend_package** — "recommend a package if I mainly watch live football"

Every reply is a strict JSON contract:
```json
{
  "answer_th": "...",
  "citations": ["catalog:c-014", "faq:f-003"],
  "action": "upgrade",
  "upsell": { "package": "TrueID Premium", "reason_th": "..." }
}
```

---

## Architecture (short version)

A **fixed, deterministic pipeline** — not a free-form agent loop, so it is predictable,
testable, and safe to run unattended:

```
/chat → request id + PII redaction → classify intent → hybrid retrieve (BM25 + dense + RRF)
      → deterministic tools (entitlement / schedule / privilege-policy)
      → LLM composes a grounded answer + structured action → Pydantic validation → response
```

- **Grounded:** answers use only retrieved sources; every claim carries a citation id.
- **Governed:** `action` and any offer come from the deterministic policy, not the LLM.
- **Resilient:** degrades gracefully — `provider` LLM → `extractive` (no LLM) and
  dense retrieval → BM25-only — so it runs **with or without an API key**.

Full design, including the OpenAI per-model-family parameter handling and the scalability
path, is in **[ARCHITECTURE.md](ARCHITECTURE.md)**.

---

## Quickstart

### A) Google Colab (how the assessment is graded)
The submission notebook clones this repo, installs, ingests, runs the tests, runs live
queries via FastAPI's in-process `TestClient`, and prints the eval metrics table. It runs
**end-to-end on a fresh CPU runtime in under ~10 minutes**, with an OpenAI key *or with no
key* (offline `extractive` mode). See **[NOTEBOOK_GUIDE.md](NOTEBOOK_GUIDE.md)**.

### B) Local
```bash
pip install -r requirements.txt    # editable install of the package
cp .env.example .env               # put your OpenAI key in .env (optional; runs without it)
make data && make ingest           # generate synthetic data + build the index
make test                          # mock LLM, no network
make eval                          # prints the metrics table
make serve                         # API on http://localhost:8000  (POST /chat)
```

### C) Docker (production path — not used inside Colab)
```bash
docker compose up --build          # api + qdrant + redis
```
> Colab has no Docker daemon, so Docker is **not** run there; it's the deploy path, and CI
> proves the image builds. This keeps "production mindset" points without risking the
> notebook run.

### Where the API key goes
- **Local / Docker:** in `.env` as `OPENAI_API_KEY=...` (`.env` is gitignored).
- **Colab:** entered at runtime via `getpass` (never committed). Leave it blank to run in
  `extractive` mode.

---

## LLMOps (embedded in the code, not just described)
- **Versioned prompts** as files in `prompts/`, selected by config.
- **Structured JSON logging** with a `request_id` + per-request **token/cost counter**.
- **Retries + timeout + fallback** in the LLM gateway (final failure → extractive, never a 500).
- **Prompt-injection hardening:** retrieved text is treated as data, never instructions.
- **PII redaction** middleware reusing the exam's Thai-ID regex.
- **Eval as a CI quality gate:** a retrieval/action regression fails the build.

**Evaluation metrics:** Hit@3, MRR, action accuracy (exact match), groundedness (citation
coverage), latency p50/p95, and cost/query — over a hand-built golden set.

## Scalability
Stateless API (horizontal scaling) · swappable vector store (in-memory → **Qdrant** behind
one `Retriever` interface) · **Redis** semantic cache for hot queries · a **model router**
(simple intents → `gpt-5.4-mini`, complex → `gpt-5.5`) · CI smoke-eval gate before deploy.

---

## Is this novel for TrueID?
TrueID has classic search + recommendation and True has launched **Mari** for customer care.
As of a public-surface check (App/Play Store changelogs, help center, recent news), a
**conversational, entitlement-aware discovery + governed-monetization** copilot does not
appear to be a shipped feature. Even if an internal pilot exists, the differentiators here —
*entitlement-aware answers, a deterministic governed action, and an eval-driven pipeline* —
stand on their own. (The rubric scores concept + execution, not patent-level novelty.)

---

## Tech stack
Python 3.10+ · FastAPI + Pydantic v2 · OpenAI Python SDK (`gpt-5.5` / `gpt-5.4-mini`,
`text-embedding-3-large`) · `rank-bm25` + NumPy/scikit-learn (hybrid retrieval) · pytest +
ruff · Docker/Compose · GitHub Actions. No agent framework, no database (synthetic data).

## Repo layout
```
configs/        app.yaml — model routing, retrieval params, feature flags
prompts/        versioned prompt files
data/           synthetic data spec + generated jsonl + golden set + index cache
src/app/        api · core · retrieval · tools · agent · llm · eval
tests/          pytest (mock LLM, no network)
notebooks/      exam.ipynb (the submission runner + report)
CLAUDE.md · PLAN.md · ARCHITECTURE.md · NOTEBOOK_GUIDE.md
```
