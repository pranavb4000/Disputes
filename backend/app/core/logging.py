"""Structured JSON logging with request context (TECH_STACK.md §14).

Uses only the standard library. Every log line is one JSON object on stdout, which
CloudWatch (AWS) or `docker compose logs` can read directly.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)

# Never log these, even if a developer passes them in `extra=`.
_SENSITIVE_KEYS = {
    "password",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "cookie",
    "secret",
    "jwt_secret",
    "aes_encryption_key",
    "blind_index_key",
}
_BEARER_RE = re.compile(r"(Bearer\s+)[A-Za-z0-9\-_.=]+", re.IGNORECASE)
_STANDARD_ATTRS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}


def _redact(value: Any) -> Any:
    if isinstance(value, str):
        return _BEARER_RE.sub(r"\1[REDACTED]", value)
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if k.lower() in _SENSITIVE_KEYS else _redact(v)) for k, v in value.items()}
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": _redact(record.getMessage()),
            "request_id": request_id_var.get(),
            "user_id": user_id_var.get(),
        }
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = "[REDACTED]" if key.lower() in _SENSITIVE_KEYS else _redact(value)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    # Uvicorn's own access log duplicates our request log; keep its error log.
    logging.getLogger("uvicorn.access").disabled = True
    for name in ("uvicorn", "uvicorn.error"):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
