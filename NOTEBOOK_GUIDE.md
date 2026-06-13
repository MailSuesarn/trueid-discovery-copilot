# NOTEBOOK_GUIDE.md — the submission notebook

Two deliverables go to the grader: (1) the filled exam notebook, (2) this GitHub repo.
The notebook's **Section 4** clones and runs this repo. **Keep the original Cell 0 timer**
(Sections 1.x need the images it downloads). Do everything else outside the notebook,
then do ONE clean **Runtime → Run all** on a fresh runtime.

> The single rule that dominates: the notebook must run end-to-end on a fresh CPU Colab.
> If it errors → 0. So Section 4 must work **with a key and with NO key** (extractive mode).

---

## Part A — Sections 1–3 fill-in answers (copy into the exam cells)

### 1.1 Crop image with mask
The mask comes from a different source than `cat.jpg`, so **sizes won't match — resize
the mask first**. The template's final line uses `COLOR_BGR2RGB`, so load the image in color.
```python
image = cv2.imread("cat.jpg")                              # fill 1: color (BGR) per template
mask  = cv2.imread("mask.jpg", cv2.IMREAD_GRAYSCALE)       # fill 1: mask as grayscale

mask = cv2.resize(mask, (image.shape[1], image.shape[0]))  # fill 2: match image size
_, mask = cv2.threshold(mask, 127, 1, cv2.THRESH_BINARY)   # fill 2: binarize to {0,1}

masked = image * mask[:, :, None]                          # fill 3: zero out masked-out regions
ys, xs = np.where(mask > 0)                                # fill 3: crop to mask bounding box
masked_image = masked[ys.min():ys.max()+1, xs.min():xs.max()+1]
```

### 1.2 Horizontal flip (no transform library)
Pure NumPy slicing. Load with `plt.imread` (already RGB; no cv2 transform used).
```python
image = plt.imread("cat.jpg")          # fill 1
h_flipped_image = image[:, ::-1]       # fill 2  (reverse the column axis)
```

### 1.3 Count distinct objects (bonus)
`shapes.jpg` is a JPEG thumbnail with noise → use Otsu + **filter tiny contours** so you
don't over-count.
```python
image = cv2.imread("shapes.jpg")                                            # fill 1
gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)                        # fill 2
_, thresh = cv2.threshold(gray_image, 0, 255,
                          cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)          # fill 3
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                               cv2.CHAIN_APPROX_SIMPLE)                     # fill 4
contours = [c for c in contours if cv2.contourArea(c) > 100]  # drop JPEG-noise specks
# keep the template's downstream lines (object_count = len(contours); drawContours; show)
```

### 2.1 Redact Thai national ID  → reused as production PII middleware in the repo
Must redact `1105267819254` and `1-2345-67890-12-3`, but **never** the `1234`. The
lookarounds prevent matching digits glued to longer numbers.
```python
masked_text = re.sub(r'(?<!\d)\d-?\d{4}-?\d{5}-?\d{2}-?\d(?!\d)', '<REDACTED>', text)
print(masked_text)
```
Senior note (put as a comment): in production you'd also validate the Thai-ID mod-11
checksum to cut false positives. (This exact regex lives in `app/api/middleware.py`.)

### 3.1 Simple CNN (PyTorch)
256 → pool → 128 → pool → 64, with 32 channels, so the FC input is `32*64*64`.
```python
# __init__
self.conv1 = nn.Conv2d(3, 16, 3, stride=1, padding=1)
self.conv2 = nn.Conv2d(16, 32, 3, stride=1, padding=1)
self.fc1   = nn.Linear(32 * 64 * 64, 4)

# forward
x = F.relu(self.conv1(x))
x = F.max_pool2d(x, 2)
x = F.relu(self.conv2(x))
x = F.max_pool2d(x, 2)
x = torch.flatten(x, 1)
x = self.fc1(x)
return x          # output shape -> torch.Size([1, 4])
```

### 3.2 Loss oscillates wildly — which hyperparameter first?
**Answer:** the **learning rate is too high → lower it first.** Wild oscillation of the
loss is the classic signature of an LR that overshoots minima. Secondary levers if it
persists: gradient clipping, an LR warmup/scheduler, or a larger batch size (less noisy
gradient estimates). But reduce the learning rate first.

---

## Part B — Section 4 cell sequence (the repo runner + report)

Replace `<YOUR_GITHUB_USERNAME>` with your handle. Order matters.

**Cell 4.1 — Markdown pitch** (no code): title, the problem (discovery + entitlement
confusion → search abandonment, missed upsell), the solution one-liner, target KPIs
(see README), and a note that the full code is the cloned repo. Mention it complements
Mari (care) by owning discovery→monetization.

**Cell 4.2 — Clone**
```python
!git clone -q https://github.com/<YOUR_GITHUB_USERNAME>/trueid-discovery-copilot.git
%cd trueid-discovery-copilot
```

**Cell 4.3 — Install** (editable install comes from `-e .` in requirements.txt)
```python
!pip install -q -r requirements.txt
```

**Cell 4.4 — API key (optional)**
```python
import os, getpass
key = getpass.getpass("OpenAI API key (press Enter to run in offline 'extractive' mode): ")
if key.strip():
    os.environ["OPENAI_API_KEY"] = key.strip()
    print("provider mode: gpt-5.5")
else:
    os.environ["LLM_MODE"] = "extractive"
    print("no key → extractive mode (still fully runnable)")
```

**Cell 4.5 — Build data + index**
```python
!python scripts/generate_data.py
!python scripts/ingest.py
```

**Cell 4.6 — Tests (prove there are real tests; mock LLM, no network)**
```python
!LLM_MODE=mock pytest -q
```

**Cell 4.7 — Live inference via in-process TestClient (zero port risk)**
```python
import json
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

queries = [
    {"user_id": "u_001", "message": "คืนนี้มีบอลพรีเมียร์ลีกไหม ดูได้เลยหรือเปล่า"},
    {"user_id": "u_001", "message": "อยากดูซีรีส์เกาหลีแนวสืบสวน เบาๆ ก่อนนอน"},
    {"user_id": "u_003", "message": "แพ็กของฉันดู Liverpool vs Arsenal ได้ไหม"},
    {"user_id": "u_002", "message": "มีสิทธิพิเศษร้านกาแฟใกล้ฉันไหม"},
    {"user_id": "u_001", "message": "recommend a package if I mainly watch live football"},
]
for q in queries:
    r = client.post("/chat", json=q)
    print(q["message"])
    print(json.dumps(r.json(), ensure_ascii=False, indent=2), "\n")
```

**Cell 4.8 — Evaluation metrics table**
```python
from app.eval.run_eval import run
import pandas as pd
results = run()                       # returns a dict of metrics
pd.DataFrame([results]).T.rename(columns={0: "value"})
```

**Cell 4.9 — (Optional, clearly marked skippable) real HTTP via uvicorn on localhost**
```python
# OPTIONAL: shows the same app over real HTTP. Safe to skip — TestClient above already
# exercised the full stack. Spins a background uvicorn on 127.0.0.1 (no internet).
import subprocess, time, requests
p = subprocess.Popen(["uvicorn", "app.main:app", "--port", "8000"])
time.sleep(4)
print(requests.post("http://127.0.0.1:8000/chat",
                    json={"user_id": "u_001", "message": "มีหนังครอบครัวสั้นๆ ไหม"}).json())
p.terminate()
```

**Cell 4.10 — Closing markdown**: deployment (Docker/compose → cloud, `docker compose up`
for api + qdrant + redis; **note Docker is the prod path, not run here**), scalability
(stateless API, swappable Qdrant index behind one interface, Redis semantic cache, model
router, CI smoke-eval gate), and LLMOps (versioned prompts, structured logging +
token/cost counter, retries/timeout/fallback, PII middleware, eval-as-quality-gate).

---

## Pre-submission checklist
- [ ] Cell 0 timer untouched; images download.
- [ ] Sections 1.1–3.2 filled (resize mask 1.1; area filter 1.3; lookaround regex 2.1; FC `32*64*64` 3.1).
- [ ] `<YOUR_GITHUB_USERNAME>` replaced; repo is public.
- [ ] **Runtime → Run all on a fresh runtime** passes WITH a key.
- [ ] Re-run once with the key prompt left blank → extractive path also passes.
- [ ] Total runtime < ~10 minutes on CPU.
