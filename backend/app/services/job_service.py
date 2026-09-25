"""Enqueue background jobs (ARCHITECTURE.md §6). The worker process runs them."""

from __future__ import annotations

import json
import logging
from typing import Any

from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.cache.redis import key
from app.models.job import Job
from app.repositories.job_repository import JobRepository
from app.utils.time import utcnow

logger = logging.getLogger(__name__)


def wake_key(queue: str) -> str:
    return key("jobs", "wake", queue)


class JobService:
    def __init__(self, db: Session, redis: Redis | None = None) -> None:
        self._db = db
        self._repo = JobRepository(db)
        self._r = redis

    def enqueue(
        self,
        job_type: str,
        payload: dict[str, Any] | None = None,
        *,
        queue: str = "light",
        priority: int = 100,
        max_attempts: int = 3,
        dedup_key: str | None = None,
        created_by: str | None = None,
    ) -> Job | None:
        """Add a job in the caller's transaction. Returns None if an identical job is already active.

        Call `notify(queue)` after the caller commits so a worker picks it up immediately.
        """
        if dedup_key and self._repo.active_exists(dedup_key):
            return None
        job = Job(
            job_type=job_type,
            queue_name=queue,
            payload=json.dumps(payload) if payload else None,
            priority=priority,
            max_attempts=max_attempts,
            dedup_key=dedup_key,
            created_by=created_by,
            run_after=utcnow(),
        )
        return self._repo.add(job)

    def notify(self, queue: str) -> None:
        if self._r is None:
            return
        try:
            self._r.lpush(wake_key(queue), "1")
            self._r.ltrim(wake_key(queue), 0, 99)
        except RedisError:
            logger.warning("Could not signal worker; it will pick the job up on its next poll")
