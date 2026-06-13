"""Structured JSON logging carrying a per-request `request_id`."""
from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar

_request_id: ContextVar[str] = ContextVar("request_id", default="-")


def set_request_id(rid: str) -> None:
    _request_id.set(rid)


def get_request_id() -> str:
    return _request_id.get()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": _request_id.get(),
        }
        extra = getattr(record, "extra_fields", None)
        if extra:
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(settings) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(getattr(logging, settings.observability.log_level, logging.INFO))


def log_event(logger: logging.Logger, msg: str, **fields) -> None:
    """Emit a structured log line, e.g. log_event(log, 'chat', intent=i, latency_ms=..., cost=...)."""
    logger.info(msg, extra={"extra_fields": fields})
