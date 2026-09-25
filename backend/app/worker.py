"""Background worker: runs queued jobs and the scheduler (ARCHITECTURE.md §6).

Run:  python -m app.worker            (all queues from WORKER_QUEUES)
      python -m app.worker ingest     (only the given queues)

Oracle is the durable queue. Redis only wakes the worker early; if Redis is down the worker
falls back to polling every WORKER_POLL_SECONDS.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import socket
import sys
import time
import traceback
from types import FrameType

from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.cache.redis import create_redis
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, request_id_var
from app.db.database import SessionLocal, get_engine
from app.jobs import handlers  # noqa: F401  (registers handlers)
from app.jobs.registry import JobContext, get_handler
from app.repositories.job_repository import JobRepository
from app.services.job_service import JobService, wake_key
from app.utils.time import utcnow

logger = logging.getLogger("app.worker")


class Worker:
    def __init__(self, settings: Settings, queues: list[str]) -> None:
        self.settings = settings
        self.queues = queues
        self.worker_id = f"{socket.gethostname()}:{os.getpid()}"
        self._stop = False
        self._last_schedule_check = 0.0
        self._last_reap = 0.0
        # Blocking BRPOP needs a socket timeout longer than the pop timeout.
        self._redis: Redis = create_redis(settings, socket_timeout=settings.worker_poll_seconds + 5)

    # --- lifecycle ------------------------------------------------------------------------------
    def stop(self, signum: int, _frame: FrameType | None) -> None:
        logger.info("Worker stopping", extra={"signal": signum})
        self._stop = True

    def run(self) -> None:
        get_engine()
        logger.info("Worker started", extra={"worker_id": self.worker_id, "queues": self.queues})
        while not self._stop:
            try:
                self._maintenance()
                if not self._run_one():
                    self._wait_for_work()
            except Exception:  # keep the loop alive; the error is logged with its traceback
                logger.exception("Worker loop error")
                time.sleep(self.settings.worker_poll_seconds)
        logger.info("Worker stopped", extra={"worker_id": self.worker_id})

    # --- maintenance: scheduler + lease reaper -----------------------------------------------------
    def _maintenance(self) -> None:
        now_mono = time.monotonic()
        if now_mono - self._last_schedule_check >= self.settings.worker_scheduler_interval_seconds:
            self._last_schedule_check = now_mono
            self._enqueue_due_schedules()
        if now_mono - self._last_reap >= 60:
            self._last_reap = now_mono
            with SessionLocal() as db:
                count = JobRepository(db).requeue_expired(utcnow())
                db.commit()
            if count:
                logger.warning("Re-queued jobs with expired leases", extra={"count": count})

    def _enqueue_due_schedules(self) -> None:
        with SessionLocal() as db:
            repo = JobRepository(db)
            jobs = JobService(db, self._redis)
            for schedule in repo.due_schedules(utcnow()):
                if not repo.try_advance_schedule(schedule, utcnow()):
                    db.rollback()
                    continue  # another worker handled this run
                payload = json.loads(schedule.payload) if schedule.payload else None
                job = jobs.enqueue(
                    schedule.job_type,
                    payload,
                    queue=schedule.queue_name,
                    dedup_key=f"schedule:{schedule.job_type}",
                    created_by="scheduler",
                )
                db.commit()
                if job is not None:
                    logger.info("Scheduled job enqueued", extra={"job_type": schedule.job_type, "job_id": job.id})

    # --- job execution -------------------------------------------------------------------------------
    def _claim(self, db: Session) -> int | None:
        repo = JobRepository(db)
        for queue in self.queues:
            for _ in range(5):  # a few retries if other workers win the race
                candidate = repo.next_candidate_id(queue, utcnow())
                if candidate is None:
                    break
                if repo.try_claim(candidate, self.worker_id, utcnow(), self.settings.worker_lease_seconds):
                    db.commit()
                    return candidate
                db.rollback()
        return None

    def _run_one(self) -> bool:
        with SessionLocal() as db:
            job_id = self._claim(db)
        if job_id is None:
            return False

        token = request_id_var.set(f"job-{job_id}")
        started = time.perf_counter()
        with SessionLocal() as db:
            repo = JobRepository(db)
            job = repo.get(job_id)
            if job is None:
                request_id_var.reset(token)
                return True
            handler = get_handler(job.job_type)

            def extend_lease() -> None:
                with SessionLocal() as lease_db:
                    JobRepository(lease_db).extend_lease(
                        job_id, self.worker_id, utcnow(), self.settings.worker_lease_seconds
                    )
                    lease_db.commit()

            try:
                if handler is None:
                    raise LookupError(f"No handler registered for job type {job.job_type}")
                handler(
                    JobContext(
                        job_id=job.id,
                        job_type=job.job_type,
                        payload=json.loads(job.payload) if job.payload else {},
                        attempt=job.attempts,
                        db=db,
                        worker_id=self.worker_id,
                        extend_lease=extend_lease,
                    )
                )
                repo.mark_done(job.id, utcnow())
                db.commit()  # handler work and DONE status commit together
                logger.info(
                    "Job done",
                    extra={
                        "job_id": job.id,
                        "job_type": job.job_type,
                        "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                    },
                )
            except Exception as exc:  # noqa: BLE001 - any handler failure must be recorded, not crash the worker
                db.rollback()
                error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=5)}"
                new_status = repo.mark_failed_or_retry(job, error, utcnow())
                db.commit()
                logger.error(
                    "Job failed",
                    extra={
                        "job_id": job.id,
                        "job_type": job.job_type,
                        "attempt": job.attempts,
                        "next_status": new_status,
                    },
                )
            finally:
                request_id_var.reset(token)
        return True

    def _wait_for_work(self) -> None:
        try:
            self._redis.brpop([wake_key(q) for q in self.queues], timeout=self.settings.worker_poll_seconds)
        except RedisError:
            time.sleep(self.settings.worker_poll_seconds)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    queues = sys.argv[1:] or settings.worker_queues
    worker = Worker(settings, queues)
    signal.signal(signal.SIGINT, worker.stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, worker.stop)
    worker.run()


if __name__ == "__main__":
    main()
