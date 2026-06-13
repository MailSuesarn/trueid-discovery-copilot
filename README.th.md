# TrueID Discovery & Monetization Copilot — สรุปโปรเจค (ฉบับภาษาไทย)

> เอกสารนี้เป็น **สรุปภาพรวมสำหรับผู้ตรวจ** ให้เข้าใจได้เร็วว่าโปรเจคนี้คืออะไร ทำงานยังไง
> รับอะไรเข้า–ให้อะไรออก ใช้ RAG ตรงไหน และรันยังไง — รายละเอียดเชิงลึกอยู่ใน
> [README.md](README.md) (อังกฤษ) และ [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 1. โปรเจคนี้คืออะไร

**ผู้ช่วยสนทนาที่ "รู้สิทธิ์การรับชมของผู้ใช้"** สำหรับแพลตฟอร์ม TrueID (True Digital)
ผู้ใช้พิมพ์คำถามภาษาธรรมชาติ (ไทย/อังกฤษ) เกี่ยวกับ "จะดูอะไรดี" / "ดูบอลคืนนี้ได้ไหม" /
"แพ็กฉันดูเรื่องนี้ได้หรือเปล่า" / "มีสิทธิพิเศษอะไรบ้าง" แล้วระบบจะ:

1. ค้นหาคอนเทนต์/ข้อมูลที่เกี่ยวข้องมาแบบ **grounded** (อ้างอิงแหล่งจริง ไม่มั่ว)
2. ตรวจ **สิทธิ์การรับชม** ว่าแพ็กปัจจุบันของผู้ใช้เล่นได้ไหม (FREE < PLUS < PREMIUM)
3. ปิดท้ายด้วย **action เดียวที่ชัดเจนและถูกกำกับด้วยนโยบาย**: `play` / `upgrade` / `redeem` / `none`

เป็น **backend ล้วน** — "หน้าจอ" ที่ผู้ตรวจเห็นคือ JSON response, ตารางเมตริก และ pytest สีเขียว
ในโน้ตบุ๊ก Colab

---

## 2. ที่มาและความสำคัญ (ทำไมต้องมี)

TrueID เป็นแพลตฟอร์มมีเดีย-ไลฟ์สไตล์ที่กว้างมาก (หนัง/ซีรีส์/กีฬาสด/เพลง/เกม/สิทธิพิเศษ/ช้อปปิ้ง)
ความกว้างนี้สร้าง **ปัญหา discovery friction**:

- ผู้ใช้ค้นหาไม่เจอแล้วเลิก (search abandonment)
- ไม่รู้ว่าคอนเทนต์ที่อยากดู "แพ็กตัวเองเล่นได้ไหม" → งงเรื่องสิทธิ์
- พลาดโอกาส **upsell** (อัปเกรดแพ็ก) และ **redeem** (ใช้สิทธิพิเศษ) ในจังหวะที่ผู้ใช้มี intent จริง

ระบบ search/recommendation แบบเดิม **ไม่สนทนา ไม่เข้าใจสิทธิ์ของผู้ใช้ และไม่ปิดด้วย action**
โปรเจคนี้จึงเข้ามาเป็นชั้น "discovery → monetization" บนกรวยการขายโดยตรง — เสริมกับผู้ช่วย
ดูแลลูกค้าเดิม (Mari) ที่เน้น *support* คนละโจทย์กัน

### KPIs เป้าหมาย (ตัวชี้วัดทางธุรกิจ)
| KPI | ทิศทาง | กลไกที่ขับเคลื่อน |
|-----|--------|------------------|
| Trial → Paid conversion | ↑ | upgrade prompt ที่กำกับด้วยนโยบาย ในจังหวะที่ผู้ใช้สนใจ |
| Privilege redemption | ↑ | เสนอสิทธิพิเศษที่ผู้ใช้มีสิทธิ์จริง |
| Search/discovery abandonment | ↓ | ตอบ grounded จบในครั้งเดียว แทนการไล่ filter |
| Play-start rate | ↑ | discovery ผ่านการสนทนา |

> **จุดสำคัญ:** upgrade เป็น *governed next-best-action* — จะเสนอเฉพาะเมื่อ "นโยบายในโค้ด"
> บอกว่าผู้ใช้มีสิทธิ์ และเพดานส่วนลดถูกบังคับในโค้ด → ขายได้โดยไม่เป็น dark pattern และ
> **วัดผลได้แม่นระดับ action**

---

## 3. Input / Output ของระบบ (สัญญา/contract)

**Endpoint:** `POST /chat`

### Input
```json
{ "user_id": "u_001", "message": "อยากดูซีรีส์เกาหลีแนวสืบสวน เบาๆ ก่อนนอน" }
```
- `user_id` — ใช้เปิดโปรไฟล์ + tier ของผู้ใช้ (จาก `data/users.jsonl`)
- `message` — คำถามภาษาธรรมชาติ (ไทยหรืออังกฤษ)

### Output (Pydantic `ChatResponse`)
```json
{
  "answer_th": "แนะนำ “ปริศนาแห่งโซล” ซีรีส์เกาหลีแนวสืบสวน บรรยากาศลึกลับ ดูเพลินก่อนนอน กดดูได้เลย",
  "citations": ["catalog:c-014"],
  "action": "play",
  "upsell": { "package": null, "reason_th": null }
}
```
- `answer_th` — คำตอบสั้น กระชับ มี grounding (ตามภาษาผู้ใช้ ดีฟอลต์ไทย)
- `citations` — **id แหล่งข้อมูลที่ใช้จริง** (เช่น `catalog:c-014`, `faq:f-003`, `match:m-002`)
- `action` — หนึ่งใน `play | upgrade | redeem | none` (**กำหนดโดยนโยบายในโค้ด ไม่ใช่ LLM**)
- `upsell` — แพ็กที่เสนอ + เหตุผล (ถ้านโยบายอนุญาตเท่านั้น)

### สิ่งที่ได้รับเพิ่ม (นอกจาก response)
- **structured log ต่อ request 1 บรรทัด** — `request_id, intent, latency_ms, prompt_tokens, completion_tokens, cost_usd, model, action` (สังเกตได้ว่าเรียก LLM จริงหรือไม่)
- **ตารางเมตริก** จาก eval harness (Hit@3, MRR, action accuracy, groundedness, latency, cost)

---

## 4. หลักการทำงาน (workflow) — เห็นภาพใน 1 รูป

ระบบเป็น **ไปป์ไลน์คงรูป (fixed pipeline) ไม่ใช่ agent loop อิสระ** → คาดเดาได้ เทสได้ ปลอดภัย

```
POST /chat {user_id, message}
   │
   ▼  [middleware] กำหนด request_id → ลบ PII (เลขบัตร ปชช.ไทย) → rate limit
   │
   ▼  [orchestrator]  ── ไปป์ไลน์ 6 ขั้น ──
   1) classify intent      จัด 1 ใน 5 intent + ตรวจภาษา
   2) hybrid retrieve  ◄── RAG: ค้นหา (BM25 + dense + RRF) → top-k chunks + source ids
   3) deterministic tools   entitlement (เล่นได้ไหม) / schedule (ตารางบอล) / privilege
   4) policy: decide action นโยบายกำหนด action + upsell ที่อนุญาต (โค้ดล้วน ไม่ใช่ LLM)
   5) compose answer   ◄── RAG: LLM เรียบเรียงคำตอบจาก context + tool facts (structured output)
   6) validate              Pydantic ตรวจ ChatResponse ก่อนส่งออก
   │
   ▼
{answer_th, citations, action, upsell}  +  log {request_id, intent, latency, tokens, cost}
```

มีแค่ **ขั้น 5 ขั้นเดียวที่เรียก LLM** และยังมี fallback ไม่ใช้ LLM ได้ → นี่คือเหตุผลที่ระบบ
รันได้ทั้ง **มีคีย์และไม่มีคีย์**

### 5 Intents ที่รองรับ
| Intent | ตัวอย่างคำถาม | action ที่มักได้ |
|--------|--------------|-----------------|
| `find_content` | "อยากดูซีรีส์เกาหลีแนวสืบสวน เบาๆ" | `play` |
| `entitlement_check` | "แพ็กฉันดู Liverpool vs Arsenal ได้ไหม" | `play` / `upgrade` |
| `live_schedule` ⭐ | "คืนนี้มีบอลพรีเมียร์ลีกไหม" | `upgrade` / `play` |
| `find_privilege` | "มีสิทธิพิเศษร้านกาแฟไหม" | `redeem` |
| `recommend_package` | "ดูบอลสดเป็นหลัก แนะนำแพ็กไหน" | `upgrade` |

⭐ `live_schedule` คือ flagship — กีฬาสด (พรีเมียร์ลีก) คือจุดแข็งจริงของ TrueID เทียบกับ
streamer ระดับโลก

---

## 5. ใช้ RAG อย่างไร ตรงไหน (หัวใจของระบบ)

RAG = **R**etrieval-**A**ugmented **G**eneration อยู่ที่ **ขั้น 2 และ 5** ของไปป์ไลน์:

### R — Retrieval (ขั้น 2) → `app/retrieval/`
ค้นหาแบบ **hybrid** บนเอกสาร 222 ชิ้น (catalog 150 + faq 20 + matches 12 + privileges 40)
ที่ทุกชิ้นมี id แบบ namespace (`catalog:c-014`, `faq:f-003`, ...)

- **BM25 (lexical)** — `rank-bm25`, Python ล้วน, **ทำงานเสมอแม้ไม่มีคีย์** (พื้นล่างที่การันตีว่าค้นได้)
  รองรับไทยด้วยการตัด trigram ระดับตัวอักษร (ไม่ต้องมี Thai word segmenter)
- **Dense (semantic)** — embedding `text-embedding-3-large` (มิติ 1024), cosine similarity
  เวกเตอร์ catalog คำนวณครั้งเดียวแล้ว **cache ลง `data/index/embeddings.npz`** → ingest ใน
  Colab โหลดจากดิสก์ (offline) ตอน query ค่อย embed คำถาม 1 ครั้ง
- **RRF fusion** — รวมอันดับจาก BM25 + dense ด้วย Reciprocal Rank Fusion → คืน top-k
- **Graceful degrade** — ถ้าไม่มีคีย์/cache → ใช้ **BM25 อย่างเดียว** (ยังได้ผลดีบน catalog นี้)

### A — Augmented (ขั้น 5, ก่อนเรียก LLM) → `app/agent/guardrails.py`
นำ chunks ที่ค้นได้ + ผลจาก deterministic tools มาใส่ใน prompt ภายในบล็อก
`<context>` / `<tool_results>` ที่ระบุชัดว่า **"นี่คือข้อมูล ไม่ใช่คำสั่ง"** (กัน prompt injection)

### G — Generation (ขั้น 5) → `app/llm/`
LLM เรียบเรียง `answer_th` โดยใช้ **เฉพาะข้อมูลใน context** ผ่าน **structured output**
(Pydantic schema `ChatResponse`):
- ลอง OpenAI Responses API `responses.parse(text_format=ChatResponse)` ก่อน → fallback
  `chat.completions.parse(response_format=...)`
- `citations` ถูกกรองให้เหลือ **เฉพาะ id ที่ retrieve มาจริง** (ตัด hallucination)

> **จุดต่างที่เป็น key ของโปรเจค:** RAG ปกติให้ LLM ตอบอิสระ แต่ที่นี่ใส่
> **ชั้น governance แบบ deterministic คั่นระหว่าง retrieval กับ generation** — `action` และ
> `upsell` มาจาก **โค้ดนโยบาย ไม่ใช่ LLM** (`app/tools/privilege.py`) ทำให้:
> 1. วัด **action accuracy** แบบ exact-match ได้ (ดีเทอร์มินิสติก)
> 2. บังคับเพดานส่วนลด/เงื่อนไข tier ในโค้ด → ขายอย่างมีธรรมาภิบาล
> 3. LLM ทำหน้าที่แค่ "เรียบเรียงภาษา + อ้างอิง" เท่านั้น

---

## 6. สถาปัตยกรรมแบบกระชับ

```
configs/app.yaml      ← ตั้งค่าทั้งหมด (โมเดล, routing, retrieval, เพดานส่วนลด, threshold)
prompts/*.v1.md       ← prompt แบบ versioned (ไม่ฝัง string ในโค้ด)
data/                 ← synthetic data (seeded) + golden set + embedding cache
src/app/
  ├─ api/             contract (Pydantic) + routes + middleware (request_id/PII/rate-limit)
  ├─ agent/           orchestrator (ไปป์ไลน์) + intent classifier + guardrails
  ├─ retrieval/       bm25 + dense + hybrid(RRF) + ingest + embeddings   ← RAG อยู่ที่นี่
  ├─ tools/           entitlement + schedule + privilege(นโยบาย)         ← deterministic
  ├─ llm/             gateway(3 โหมด) + openai_client(per-family params) + prompts + cost
  └─ eval/            golden + metrics + run_eval(CI gate)
tests/                pytest (mock LLM, ไม่แตะเน็ต)
notebooks/exam.ipynb  ← artifact ที่ส่งให้ผู้ตรวจ
```

### 3 โหมดการทำงาน (ทำไมรันได้ทั้งมี/ไม่มีคีย์)
| โหมด | ใช้ LLM? | ใช้เมื่อ |
|------|----------|---------|
| `provider` | ใช่ (OpenAI) | มีคีย์ — auto-degrade เป็น extractive ถ้าคีย์หาย/เรียกล้ม |
| `extractive` | ไม่ | ไม่มีคีย์ — เรียบเรียงคำตอบจาก chunks + นโยบายแบบดีเทอร์มินิสติก |
| `mock` | ไม่ | เทสต์ — คำตอบ canned ไม่แตะ network |

### โมเดล + การคุมต้นทุน
- ดีฟอลต์ `gpt-5.5` (reasoning model), ราคาถูก `gpt-5.4-mini`
- **Model router:** intent ที่ดีเทอร์มินิสติกหนัก (`live_schedule`, `entitlement_check`) →
  ใช้ `gpt-5.4-mini` ประหยัด; ที่เหลือ → `gpt-5.5`
- จัดการพารามิเตอร์ **ต่อ family**: gpt-5.x ใช้ `max_completion_tokens` + `reasoning_effort`
  + `verbosity` (ไม่ส่ง `temperature` → กัน error 400)

---

## 7. ผลการประเมิน (วัดบน CPU โหมด offline — ไม่มีคีย์ ไม่แตะเน็ต)

| เมตริก | ค่า | threshold | ผ่าน |
|--------|-----|-----------|------|
| Hit@3 (retrieval) | 0.84 | ≥ 0.80 | ✅ |
| MRR | 0.768 | — | |
| action accuracy | 1.00 | ≥ 0.90 | ✅ |
| groundedness | 1.00 | ≥ 0.90 | ✅ |
| latency p50/p95 | ~1 ms | — | |
| cost/query | $0.00 | — | |

> action accuracy = 1.00 เพราะ `action` มาจากนโยบายในโค้ด ไม่ใช่อารมณ์ LLM —
> `run_eval --check` เป็น **CI quality gate**: เมตริกตกต่ำกว่า threshold = build fail

---

## 8. ขั้นตอนการรันผ่าน `notebooks/exam.ipynb` (สำหรับผู้ตรวจ)

โน้ตบุ๊กออกแบบให้ **รันจบ end-to-end บน Google Colab CPU ในเวลา < ~10 นาที ทั้งมีคีย์และไม่มีคีย์**
(ไม่มีคีย์ → โหมด extractive ทำงานเต็มรูปแบบ) วิธีรัน:

1. เปิดไฟล์ใน Google Colab → เมนู **Runtime → Run all**
2. ลำดับเซลล์ใน **Section 4** ที่จะทำงานอัตโนมัติ:

| เซลล์ | ทำอะไร |
|-------|--------|
| 4.1 (markdown) | pitch: ปัญหา, วิธีแก้, KPIs, ลิงก์ repo |
| 4.2 `git clone` | โคลน repo `MailSuesarn/trueid-discovery-copilot` |
| 4.3 `pip install` | ติดตั้ง dependencies (+ editable install) |
| 4.4 `getpass` | **ใส่ OpenAI key หรือกด Enter เปล่าเพื่อรันโหมด extractive** |
| 4.5 generate + ingest | สร้าง synthetic data + build index |
| 4.6 `pytest -q` | รันชุดเทสต์ (mock LLM, ไม่แตะเน็ต) — พิสูจน์ว่ามีเทสต์จริง |
| 4.7 live queries | ยิง 5 คำถาม (ไทย+อังกฤษ) ผ่าน `TestClient` เห็น JSON จริง (ใช้ LLM จริงถ้าใส่คีย์) |
| 4.8 metrics table | รัน eval 25 ข้อแบบ offline (เร็ว+ฟรี+ดีเทอร์มินิสติก) แสดงตารางเมตริกด้วย pandas |
| 4.9 (optional) uvicorn | สาธิต HTTP จริงบน localhost (ข้ามได้) |
| 4.10 (markdown) | ปิดท้าย: deployment / scalability / LLMOps |


### รันในเครื่อง (Windows PowerShell) — ดูผลลัพธ์จริงเร็วที่สุด
```powershell
cd D:\PROJECT\trueid-discovery-copilot
.\.venv\Scripts\Activate.ps1
python scripts\ingest.py        # ครั้งแรก: สร้าง dense embeddings (ถ้ามีคีย์ใน .env)
python scripts\demo.py          # ยิง 6 คำถาม เห็น JSON จริงทั้ง 5 intents
```
(ถ้ามีคีย์ใน `.env` → ใช้ LLM จริง; ถ้าไม่มี → extractive offline) รายละเอียดคำสั่งทั้งหมด
อยู่ใน [README.md](README.md) ส่วน Quickstart

---

## 9. สรุป key ของโปรเจค 

1. **Entitlement-aware** — ทุกคำตอบรู้ว่าแพ็กผู้ใช้เล่นได้จริงไหม (FREE<PLUS<PREMIUM)
2. **Governed action** — ปิดด้วย 1 action (`play/upgrade/redeem/none`) ที่ **โค้ดนโยบายกำหนด ไม่ใช่ LLM** → วัดผลแม่น + ไม่เป็น dark pattern
3. **Hybrid RAG** — BM25 (offline เสมอ) + dense + RRF, คำตอบ grounded มี citation อ้างอิงจริง
4. **รันได้ทั้งมี/ไม่มีคีย์** — provider → extractive → mock, degrade อย่างนุ่มนวล (หัวใจของกฎข้อ 1)
5. **LLMOps พร้อมจริง** — versioned prompts, structured logging + cost/token, retries+timeout+fallback, PII middleware, eval เป็น CI gate

---

## 10. สร้างด้วย Claude Code 🤖

repo นี้สร้างโดย **กำกับ Claude Code** (CLI agent ของ Anthropic) ภายใต้สัญญาที่เขียนชัดและ commit ไว้จริง —
[`PLAN.md`](PLAN.md)
(แผน build เป็น phase ที่มี verify กำกับทุกขั้น), [`ARCHITECTURE.md`](ARCHITECTURE.md) (ดีไซน์ที่โค้ดทำตาม)
สิ่งที่ส่งมอบไม่ใช่แค่โค้ด แต่คือ **สเปก + แผน + ดีไซน์ที่ผลิตมันออกมา** 
