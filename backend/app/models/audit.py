"""Append-only, tamper-evident audit log (ARCHITECTURE.md §5.8).

Each row stores SHA-256(previous row hash + this row's content). The single-row `audit_chain`
table holds the latest hash and is locked (SELECT ... FOR UPDATE) while a row is appended,
so concurrent writers cannot fork the chain.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import TIMESTAMP, Identity, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.utils.time import utcnow

GENESIS_HASH = "0" * 64


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(TIMESTAMP(), default=utcnow, nullable=False, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(Integer, index=True)
    actor_username: Mapped[str | None] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)  # SUCCESS | FAILURE
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[str | None] = mapped_column(String(100))
    module_code: Mapped[str | None] = mapped_column(String(20))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    request_id: Mapped[str | None] = mapped_column(String(64))
    details: Mapped[str | None] = mapped_column(Text)  # JSON text; never contains secrets
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    row_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class AuditChain(Base):
    __tablename__ = "audit_chain"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # always 1
    last_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(), default=utcnow, nullable=False)
