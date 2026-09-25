"""Job queue claim logic, audit hash chain and local file storage."""

from __future__ import annotations

import io
from datetime import timedelta
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.models.job import JobStatus
from app.repositories.job_repository import JobRepository
from app.services.audit_service import AuditService
from app.services.job_service import JobService, wake_key
from app.storage.local import LocalFileStorage
from app.utils.time import utcnow
from tests.fakes import FakeRedis


def test_enqueue_dedup_and_notify(db: Session, seeded: object, redis: FakeRedis) -> None:
    service = JobService(db, redis)
    first = service.enqueue("SYSTEM_HEARTBEAT", {"a": 1}, dedup_key="hb")
    duplicate = service.enqueue("SYSTEM_HEARTBEAT", dedup_key="hb")
    db.commit()
    service.notify("light")
    assert first is not None and duplicate is None
    assert redis.brpop([wake_key("light")]) is not None


def test_only_one_worker_can_claim_a_job(db: Session, seeded: object) -> None:
    job = JobService(db).enqueue("SYSTEM_HEARTBEAT", queue="light")
    db.commit()
    repo = JobRepository(db)
    now = utcnow()
    assert repo.next_candidate_id("light", now) == job.id
    assert repo.try_claim(job.id, "worker-a", now, 60) is True
    assert repo.try_claim(job.id, "worker-b", now, 60) is False  # lost the race
    db.commit()
    assert repo.next_candidate_id("light", now) is None


def test_failed_job_retries_then_fails(db: Session, seeded: object) -> None:
    job = JobService(db).enqueue("X", max_attempts=2)
    db.commit()
    repo = JobRepository(db)
    repo.try_claim(job.id, "w", utcnow(), 60)
    db.commit()
    db.refresh(job)
    assert repo.mark_failed_or_retry(job, "boom", utcnow()) == JobStatus.QUEUED
    db.commit()
    repo.try_claim(job.id, "w", utcnow() + timedelta(hours=2), 60)
    db.commit()
    db.refresh(job)
    assert repo.mark_failed_or_retry(job, "boom again", utcnow()) == JobStatus.FAILED


def test_expired_leases_are_requeued(db: Session, seeded: object) -> None:
    job = JobService(db).enqueue("X")
    db.commit()
    repo = JobRepository(db)
    repo.try_claim(job.id, "w", utcnow() - timedelta(hours=1), 60)
    db.commit()
    assert repo.requeue_expired(utcnow()) == 1


def test_audit_chain_detects_tampering(db: Session, seeded: object) -> None:
    audit = AuditService(db)
    audit.record("LOGIN", actor_username="a")
    second = audit.record("LOGOUT", actor_username="a")
    audit.record("LOGIN", actor_username="b")
    db.commit()
    assert audit.verify_chain() == (True, None)
    second.action = "SOMETHING_ELSE"
    db.commit()
    assert audit.verify_chain() == (False, second.id)


def test_local_storage_round_trip_and_path_safety(tmp_path: Path) -> None:
    storage = LocalFileStorage(tmp_path)
    storage.put("uploads/2026/09/file.xlsx", io.BytesIO(b"data"))
    assert storage.exists("uploads/2026/09/file.xlsx")
    with storage.open("uploads/2026/09/file.xlsx") as fh:
        assert fh.read() == b"data"
    assert storage.scan_status("uploads/2026/09/file.xlsx") == "NO_THREATS_FOUND"
    for bad in ("../secret", "/etc/passwd", "a/../../b", "a//b"):
        with pytest.raises(ValueError):
            storage.put(bad, io.BytesIO(b"x"))
