"""Test config. Forces LLM_MODE=mock so the suite NEVER hits the network."""
from __future__ import annotations

import os

os.environ.setdefault("LLM_MODE", "mock")  # must be set before importing the app

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
