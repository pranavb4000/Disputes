"""Data access for the audit log and its hash chain."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import GENESIS_HASH, AuditChain, AuditLog
from app.utils.time import utcnow


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def lock_chain_head(self) -> AuditChain:
        """Lock the chain head row for this transaction (serialises audit appends)."""
        head = self._db.execute(select(AuditChain).where(AuditChain.id == 1).with_for_update()).scalar_one_or_none()
        if head is None:  # first ever write (normally created by the migration)
            head = AuditChain(id=1, last_hash=GENESIS_HASH, updated_at=utcnow())
            self._db.add(head)
            self._db.flush()
        return head

    def append(self, entry: AuditLog, head: AuditChain) -> AuditLog:
        self._db.add(entry)
        head.last_hash = entry.row_hash
        head.updated_at = utcnow()
        self._db.flush()
        return entry

    def recent_for_user(self, user_id: int, limit: int = 10) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.actor_user_id == user_id)
            .order_by(AuditLog.occurred_at.desc(), AuditLog.id.desc())
            .limit(limit)
        )
        return list(self._db.execute(stmt).scalars())

    def all_in_order(self) -> list[AuditLog]:
        return list(self._db.execute(select(AuditLog).order_by(AuditLog.id)).scalars())
