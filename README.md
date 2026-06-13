<p align="center">
  <img src="docs/hero.png" alt="TrueID Discovery & Monetization Copilot" width="100%">
</p>

<h1 align="center">TrueID Discovery & Monetization Copilot</h1>

<p align="center">
  <em>An <b>entitlement-aware</b> conversational copilot that finds content (incl. live sports),
  checks whether <b>your</b> package can play it, surfaces relevant privileges,
  and ends with <b>one honest, governed action</b>.</em>
</p>

<p align="center">
  <code>play</code> · <code>upgrade</code> · <code>redeem</code> · <code>none</code> &nbsp;|&nbsp;
  FastAPI · Hybrid RAG (BM25 + dense + RRF) · Pydantic structured output · eval-as-CI-gate
</p>

<p align="center">
  🇹🇭 <a href="README.th.md"><b>อ่านสรุปฉบับภาษาไทย (สำหรับผู้ตรวจ)</b></a> &nbsp;·&nbsp;
  📐 <a href="ARCHITECTURE.md">Architecture</a> &nbsp;·&nbsp;
  📓 <a href="notebooks/exam.ipynb">Submission notebook</a>
</p>

---

## What & why

TrueID is a broad media-lifestyle platform (watch, listen, live sports, games, privileges, commerce).
That breadth creates **discovery friction**: users abandon search, don't know if their package can
play something, and miss the upgrade or privilege that fits them. Classic search rails don't
*converse*, don't reason about **entitlement**, and don't close with an action.

This copilot sits on the **discovery → monetization** moment — complementing True's care assistant
(Mari, which owns support). It turns a natural-language question into a grounded answer **plus one
governed next step**.

**Target KPIs:** trial→paid conversion ↑ · privilege redemption ↑ · search abandonment ↓ · play-start ↑.
The upgrade is a *governed next-best-action* — offered **only when a deterministic policy says so**,
discount capped **in code**. Monetization without dark patterns, and **measurable to the exact action**.

## What it does — 5 intents, 1 JSON contract

| Intent | Example | Typical action |
|--------|---------|----------------|
| `find_content` | "อยากดูซีรีส์เกาหลีแนวสืบสวน เบาๆ" | `play` |
| `entitlement_check` | "แพ็กของฉันดู Liverpool vs Arsenal ได้ไหม" | `play` / `upgrade` |
| `live_schedule` ⭐ | "คืนนี้มีบอลพรีเมียร์ลีกไหม" | `upgrade` / `play` |
| `find_privilege` | "มีสิทธิพิเศษร้านกาแฟไหม" | `redeem` |
| `recommend_package` | "recommend a package for live football" | `upgrade` |

⭐ Live sports (Premier League) is TrueID's real moat vs global streamers.

**Input** `POST /chat` → **Output** (Pydantic-validated):
```json
{
  "answer_th": "แนะนำ ปริศนาแห่งโซล — ซีรีส์เกาหลีแนวสืบสวน ดูเพลินก่อนนอน กดดูได้เลย",
  "citations": ["catalog:c-014"],
  "action": "play",
  "upsell": { "package": null, "reason_th": null }
}
```

## How it works

A **fixed, deterministic pipeline** — not a free-form agent loop, so it's predictable, testable, and safe:

```
POST /chat
  → request_id + PII redaction (Thai-ID regex) + rate limit
  → 1) classify intent          (+ language)
  → 2) hybrid retrieve          BM25 + dense + RRF   ◄── RAG: Retrieval
  → 3) deterministic tools       entitlement / schedule / privilege
  → 4) policy: decide action     governed action + upsell (code, NOT the LLM)
  → 5) compose answer            LLM grounded in context  ◄── RAG: Augment + Generate
  → 6) validate (Pydantic) → { answer_th, citations, action, upsell }  + structured log
```

Only **step 5 calls the LLM**, and it has a no-LLM fallback — that's why the whole thing runs
**with or without an API key**.

### Where RAG lives (the core)
- **Retrieve** (`app/retrieval/`) — hybrid over 222 namespaced docs (`catalog:c-014`, `faq:f-003`, …):
  **BM25** (always-on, offline, Thai via char-trigrams) + **dense** (`text-embedding-3-large`, 1024-d,
  cached to `data/index/embeddings.npz`) fused with **Reciprocal Rank Fusion**. No key/cache → BM25-only.
- **Augment** (`app/agent/guardrails.py`) — retrieved chunks + tool facts go into `<context>` /
  `<tool_results>` blocks, explicitly framed as *data, not instructions* (prompt-injection hardening).
- **Generate** (`app/llm/`) — the LLM writes `answer_th` via **structured output** (OpenAI
  `responses.parse(text_format=ChatResponse)` → `chat.completions.parse` fallback). Citations are
  filtered to **ids that were actually retrieved** (no hallucinated sources).

> **The key twist:** a **deterministic governance layer sits between retrieval and generation**.
> `action` + `upsell` come from `app/tools/privilege.py` (code), not the LLM — making action
> accuracy an exact-match metric, enforcing the discount ceiling, and leaving the LLM to do only
> phrasing + citing.

## Results (offline path — no key, no network, on CPU)

| metric | value | threshold |
|--------|-------|-----------|
| Hit@3 | **0.84** | ≥ 0.80 ✅ |
| MRR | 0.768 | — |
| action accuracy | **1.00** | ≥ 0.90 ✅ |
| groundedness | **1.00** | ≥ 0.90 ✅ |
| latency p50 / p95 | ~1 ms | — |
| cost / query | $0.00 | — |

`python -m app.eval.run_eval --check` is the **CI quality gate** — any drop below threshold fails the build.

## Quickstart

**Google Colab (how it's graded)** — open [`notebooks/exam.ipynb`](notebooks/exam.ipynb) → *Runtime → Run all*.
It clones, installs, ingests, runs pytest, fires 5 live queries, and prints the metrics table —
**end-to-end on a fresh CPU runtime in <~10 min, with or without a key** (no key → offline mode).

**Local (cross-platform):**
```bash
pip install -r requirements.txt        # editable install of the package
python scripts/generate_data.py        # seeded synthetic data
python scripts/ingest.py               # build index (BM25 always; dense if a key is set)
LLM_MODE=mock pytest -q                 # tests: mock LLM, no network
python -m app.eval.run_eval --check     # metrics table + CI gate
python scripts/demo.py                  # ▶ see real /chat output for all 5 intents
```
`make data | ingest | test | eval | lint | serve` wrap these on systems with `make`.

**API key:** put `OPENAI_API_KEY=...` in `.env` (gitignored, auto-loaded) → `demo.py` uses the real
LLM; no key → deterministic offline mode. (Colab prompts for the key via `getpass`.)

<details>
<summary><b>Windows PowerShell (no <code>make</code>) — full steps</b></summary>

> Use **Python 3.11**: `numpy==2.2.1` has no Windows wheels for 3.13/3.14 (source build fails).

```powershell
py -3.11 -m venv .venv                  # if `py -3.11` is missing: install via winget/uv first
.\.venv\Scripts\Activate.ps1            # blocked? Set-ExecutionPolicy -Scope Process Bypass
python -m pip install -r requirements.txt
python scripts\generate_data.py
python scripts\ingest.py
$env:LLM_MODE='mock'; python -m pytest -q
python -m app.eval.run_eval --check
python -m ruff check src tests scripts
Remove-Item Env:\LLM_MODE; python scripts\demo.py     # uses .env key if present
```
| `make` | PowerShell |
|--------|------------|
| `make data` | `python scripts\generate_data.py` |
| `make ingest` | `python scripts\ingest.py` |
| `make test` | `$env:LLM_MODE='mock'; python -m pytest -q` |
| `make eval` | `$env:LLM_MODE='mock'; python -m app.eval.run_eval` |
| `make serve` | `python -m uvicorn app.main:app --port 8000` |

Not activating the venv? Prefix every `python` with `.\.venv\Scripts\python.exe`.
</details>

<details>
<summary><b>Docker (production path — not run in Colab)</b></summary>

```bash
docker compose up --build              # api + qdrant + redis
```
CI proves the image builds. Colab has no Docker daemon, so it's never run there.
</details>

## Production posture

- **LLMOps:** versioned prompts · structured JSON logs with `request_id` + token/cost counter ·
  retries + timeout + fallback (provider→extractive, never a 500) · PII middleware · eval-as-CI-gate.
- **Scalability:** stateless API · swappable vector store (in-memory → **Qdrant** behind one
  `Retriever` interface) · **Redis** semantic cache · **model router** (simple intents →
  `gpt-5.4-mini`, complex → `gpt-5.5`).
- **Per-family LLM params:** reasoning models get `max_completion_tokens` + `reasoning_effort` +
  `verbosity` (no `temperature`) — never a 400.

## Built with Claude Code 🤖

This repo was built by orchestrating **Claude Code** (Anthropic's CLI agent) under an explicit,
committed contract:

- [`CLAUDE.md`](CLAUDE.md) — the operating rules the agent followed (the "#1 rule", conventions, DoD).
- [`PLAN.md`](PLAN.md) — the phased build order, each phase gated by verify commands.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — the design the code implements.

The deliverable isn't just code — it's the **spec + plan + design that produced it**. 

## Tech stack & layout

Python 3.11 · FastAPI + Pydantic v2 · OpenAI SDK (`gpt-5.5` / `gpt-5.4-mini`, `text-embedding-3-large`)
· `rank-bm25` + NumPy/scikit-learn · pytest + ruff · Docker · GitHub Actions. No agent framework, no DB.

```
configs/   app.yaml (model routing, retrieval, thresholds)   prompts/  versioned prompts
src/app/   api · core · retrieval · tools · agent · llm · eval
data/      synthetic data + golden set + embedding cache      tests/    pytest (mock, no network)
notebooks/ exam.ipynb (submission runner + report)            scripts/  generate_data · ingest · demo
```
