"""Request middleware: request id, PII redaction, rate limit.

`redact_pii` is production-ready and reuses the exam Section 2.1 Thai-ID regex — a tiny
exam question promoted to a real production component (unit-tested in tests/test_pii.py).
The middleware *wiring* onto the app is implemented in Phase 5.
"""
from __future__ import annotations

import re

# Thai national ID structure 1-4-5-2-1. Lookarounds stop it matching digits glued to a
# longer run, so a bare '1234' is never redacted.
THAI_ID_RE = re.compile(r"(?<!\d)\d-?\d{4}-?\d{5}-?\d{2}-?\d(?!\d)")


def redact_pii(text: str) -> str:
    """Replace Thai national IDs with <REDACTED>. Reused from exam Section 2.1."""
    return THAI_ID_RE.sub("<REDACTED>", text)


# TODO(claude-code, Phase 5):
#   - RequestIdMiddleware: generate a uuid4, call core.logging.set_request_id, add header.
#   - Apply redact_pii to the inbound message before it reaches the orchestrator.
#   - RateLimitMiddleware: naive per-minute counter from guardrails.rate_limit_per_min.
