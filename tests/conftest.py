"""Test config. Forces LLM_MODE=mock so the suite NEVER hits the network."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

os.environ["LLM_MODE"] = "mock"  # force mock — the suite must never hit the network
os.environ.pop("OPENAI_API_KEY", None)

# Generate synthetic data once for the whole test run (cheap, deterministic, seeded).
_DATA_DIR = Path("data")
if not (_DATA_DIR / "catalog.jsonl").exists():
    subprocess.run([sys.executable, "scripts/generate_data.py"], check=True)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

# Importing the app triggers app.core.config, which calls load_dotenv(). If a local .env
# exists with a real key, that would re-inject OPENAI_API_KEY and make embed_query() (called
# during retrieval) hit the network. Re-pop AFTER import so the suite stays hermetic — mock
# mode, no key, no network — regardless of any local .env. (In CI there is no .env anyway.)
os.environ.pop("OPENAI_API_KEY", None)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
