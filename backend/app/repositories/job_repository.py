"""Data access for the Oracle job queue.

Claiming uses an optimistic, portable pattern (ARCHITECTURE.md §6.2):
  1. read the id of the next eligible job (no lock), then
  2. UPDATE ... WHERE id = :id AND status = 'QUEUED'.
If another worker won the race, step 2 updates 0 rows and we simply try again.
(Oracle rejects FOR UPDATE combined with FETCH FIRST, so we avoid that construct.)
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import CursorResult, select, update
from sqlalchemy.orm import Session

from app.models.job import Job, JobSchedule, JobStatus


class JobRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, job: Job) -> Job:
        self._db.add(job)
        self._db.flush()
        return job

    def get(self, job_id: int) -> Job | None:
        return self._db.get(Job, job_id)

    def active_exists(self, dedup_key: str) -> bool:
        stmt = select(Job.id).where(Job.dedup_key == dedup_key, Job.status.in_(JobStatus.ACTIVE)).limit(1)
        return self._db.execute(stmt).first() is not None

    def next_candidate_id(self, queue: str, now: datetime) -> int | None:
        stmt = (
            select(Job.id)
            .where(Job.status == JobStatus.QUEUED, Job.queue_name == queue, Job.run_after <= now)
            .order_by(Job.priority, Job.id)
            .limit(1)
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def try_claim(self, job_id: int, worker_id: str, now: datetime, lease_seconds: int) -> bool:
        result = self._db.execute(
            update(Job)
            .where(Job.id == job_id, Job.status == JobStatus.QUEUED)
            .values(
                status=JobStatus.RUNNING,
                locked_by=worker_id,
                lease_until=now + timedelta(seconds=lease_seconds),
                attempts=Job.attempts + 1,
                updated_at=now,
            )
            .execution_options(synchronize_session=False)
        )
        return _rowcount(result) == 1

    def mark_done(self, job_id: int, now: datetime) -> None:
        self._db.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(status=JobStatus.DONE, finished_at=now, locked_by=None, lease_until=None, updated_at=now)
            .execution_options(synchronize_session=False)
        )

    def mark_failed_or_retry(self, job: Job, error: str, now: datetime) -> str:
        if job.attempts < job.max_attempts:
            backoff = timedelta(seconds=min(30 * 2 ** (job.attempts - 1), 3600))
            values = {"status": JobStatus.QUEUED, "run_after": now + backoff}
        else:
            values = {"status": JobStatus.FAILED, "finished_at": now}
        self._db.execute(
            update(Job)
            .where(Job.id == job.id)
            .values(**values, last_error=error[:2000], locked_by=None, lease_until=None, updated_at=now)
            .execution_options(synchronize_session=False)
        )
        return str(values["status"])

    def extend_lease(self, job_id: int, worker_id: str, now: datetime, lease_seconds: int) -> None:
        self._db.execute(
            update(Job)
            .where(Job.id == job_id, Job.locked_by == worker_id, Job.status == JobStatus.RUNNING)
            .values(lease_until=now + timedelta(seconds=lease_seconds), updated_at=now)
            .execution_options(synchronize_session=False)
        )

    def requeue_expired(self, now: datetime) -> int:
        result = self._db.execute(
            update(Job)
            .where(Job.status == JobStatus.RUNNING, Job.lease_until < now)
            .values(status=JobStatus.QUEUED, locked_by=None, lease_until=None, updated_at=now)
            .execution_options(synchronize_session=False)
        )
        return _rowcount(result)

    # --- schedules ---------------------------------------------------------------------------

    def due_schedules(self, now: datetime) -> list[JobSchedule]:
        stmt = select(JobSchedule).where(JobSchedule.is_enabled.is_(True), JobSchedule.next_run_at <= now)
        return list(self._db.execute(stmt).scalars())

    def try_advance_schedule(self, schedule: JobSchedule, now: datetime) -> bool:
        """Move next_run_at forward only if nobody else did (exactly-once enqueue)."""
        next_run = now + timedelta(seconds=schedule.interval_seconds)
        result = self._db.execute(
            update(JobSchedule)
            .where(JobSchedule.id == schedule.id, JobSchedule.next_run_at == schedule.next_run_at)
            .values(next_run_at=next_run, last_run_at=now)
            .execution_options(synchronize_session=False)
        )
        return _rowcount(result) == 1

    def get_schedule(self, job_type: str) -> JobSchedule | None:
        return self._db.execute(select(JobSchedule).where(JobSchedule.job_type == job_type)).scalar_one_or_none()

    def add_schedule(self, schedule: JobSchedule) -> None:
        self._db.add(schedule)


def _rowcount(result: object) -> int:
    return result.rowcount if isinstance(result, CursorResult) else 0
