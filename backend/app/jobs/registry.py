"""Maps job_type -> handler. Handlers are thin: they call services, like API routes do.

Handlers MUST be idempotent: after a crash a job can run again (ARCHITECTURE.md §6.2).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

JobHandler = Callable[["JobContext"], None]


@dataclass
class JobContext:
    job_id: int
    job_type: str
    payload: dict[str, Any]
    attempt: int
    db: Session
    worker_id: str
    extend_lease: Callable[[], None]


_HANDLERS: dict[str, JobHandler] = {}


def register(job_type: str) -> Callable[[JobHandler], JobHandler]:
    def decorator(func: JobHandler) -> JobHandler:
        if job_type in _HANDLERS:
            raise ValueError(f"Duplicate handler for job type {job_type}")
        _HANDLERS[job_type] = func
        return func

    return decorator


def get_handler(job_type: str) -> JobHandler | None:
    return _HANDLERS.get(job_type)


def registered_types() -> list[str]:
    return sorted(_HANDLERS)
