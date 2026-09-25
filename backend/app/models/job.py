"""Background job queue stored in Oracle (ARCHITECTURE.md §6, approved design)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import TIMESTAMP, Boolean, Identity, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.utils.time import utcnow


class JobStatus:
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    ACTIVE = (QUEUED, RUNNING)


class Job(TimestampMixin, Base):
    __tablename__ = "job"
    __table_args__ = (
        Index("ix_job_claim", "status", "queue_name", "run_after", "priority"),
        # Only one QUEUED/RUNNING job per dedup_key (function-based index; NULL keys are not indexed).
        Index(
            "ux_job_active_dedup", text("(CASE WHEN status IN ('QUEUED','RUNNING') THEN dedup_key END)"), unique=True
        ),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    queue_name: Mapped[str] = mapped_column(String(30), nullable=False, default="light")
    payload: Mapped[str | None] = mapped_column(Text)  # JSON text
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=JobStatus.QUEUED)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    run_after: Mapped[datetime] = mapped_column(TIMESTAMP(), nullable=False, default=utcnow)
    locked_by: Mapped[str | None] = mapped_column(String(100))
    lease_until: Mapped[datetime | None] = mapped_column(TIMESTAMP())
    dedup_key: Mapped[str | None] = mapped_column(String(200))
    last_error: Mapped[str | None] = mapped_column(String(2000))
    created_by: Mapped[str | None] = mapped_column(String(100))
    finished_at: Mapped[datetime | None] = mapped_column(TIMESTAMP())


class JobSchedule(Base):
    __tablename__ = "job_schedule"

    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    job_type: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    queue_name: Mapped[str] = mapped_column(String(30), nullable=False, default="light")
    payload: Mapped[str | None] = mapped_column(Text)
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    next_run_at: Mapped[datetime] = mapped_column(TIMESTAMP(), nullable=False, default=utcnow)
    last_run_at: Mapped[datetime | None] = mapped_column(TIMESTAMP())
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
