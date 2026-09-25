"""Business-level audit trail. Writes join the caller's transaction (commit together or not at all)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import request_id_var
from app.models.audit import GENESIS_HASH, AuditLog
from app.repositories.audit_repository import AuditRepository
from app.utils.time import utcnow


@dataclass(frozen=True)
class AuditContext:
    ip_address: str | None = None
    request_id: str | None = None


def _row_hash(prev_hash: str, entry: AuditLog) -> str:
    content = json.dumps(
        {
            "prev": prev_hash,
            "at": entry.occurred_at.isoformat(),
            "actor": entry.actor_user_id,
            "username": entry.actor_username,
            "action": entry.action,
            "outcome": entry.outcome,
            "entity_type": entry.entity_type,
            "entity_id": entry.entity_id,
            "module": entry.module_code,
            "ip": entry.ip_address,
            "request_id": entry.request_id,
            "details": entry.details,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(content.encode()).hexdigest()


class AuditService:
    def __init__(self, db: Session) -> None:
        self._repo = AuditRepository(db)

    def record(
        self,
        action: str,
        *,
        outcome: str = "SUCCESS",
        actor_user_id: int | None = None,
        actor_username: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        module_code: str | None = None,
        details: dict[str, Any] | None = None,
        context: AuditContext | None = None,
    ) -> AuditLog:
        ctx = context or AuditContext()
        head = self._repo.lock_chain_head()
        entry = AuditLog(
            occurred_at=utcnow(),
            actor_user_id=actor_user_id,
            actor_username=actor_username,
            action=action,
            outcome=outcome,
            entity_type=entity_type,
            entity_id=entity_id,
            module_code=module_code,
            ip_address=ctx.ip_address,
            request_id=ctx.request_id or request_id_var.get(),
            details=json.dumps(details, sort_keys=True, default=str) if details else None,
            prev_hash=head.last_hash,
        )
        entry.row_hash = _row_hash(head.last_hash, entry)
        return self._repo.append(entry, head)

    def verify_chain(self) -> tuple[bool, int | None]:
        """Recompute every hash. Returns (ok, id of first broken row)."""
        prev = GENESIS_HASH
        for entry in self._repo.all_in_order():
            if entry.prev_hash != prev or _row_hash(prev, entry) != entry.row_hash:
                return False, entry.id
            prev = entry.row_hash
        return True, None
