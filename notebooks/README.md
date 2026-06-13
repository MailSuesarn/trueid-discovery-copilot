# notebooks/

`exam.ipynb` lives here — the filled assessment notebook that is submitted.

It is the **runner + report** for this repo: its Section 4 clones the repo, installs,
ingests, runs pytest, runs live `TestClient` queries, prints the eval metrics table, and
ends with the deployment/scaling/LLMOps markdown.

Build it from the original exam notebook by following **`../NOTEBOOK_GUIDE.md`**, which
contains the exact Section 1–3 fill-in answers and the Section 4 cell sequence.

Do not commit a notebook that hard-codes any API key. The key is entered via `getpass`
at runtime (or left blank to run in offline `extractive` mode).
