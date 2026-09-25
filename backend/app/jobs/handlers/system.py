"""System jobs that prove the worker and scheduler work end to end."""

from __future__ import annotations

import logging

from app.jobs.registry import JobContext, register
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

HEARTBEAT = "SYSTEM_HEARTBEAT"
VERIFY_AUDIT_CHAIN = "SYSTEM_VERIFY_AUDIT_CHAIN"


@register(HEARTBEAT)
def heartbeat(ctx: JobContext) -> None:
    logger.info("Worker heartbeat", extra={"job_id": ctx.job_id, "worker_id": ctx.worker_id})


@register(VERIFY_AUDIT_CHAIN)
def verify_audit_chain(ctx: JobContext) -> None:
    ok, broken_id = AuditService(ctx.db).verify_chain()
    if ok:
        logger.info("Audit chain verified", extra={"job_id": ctx.job_id})
    else:
        logger.error("AUDIT CHAIN BROKEN", extra={"job_id": ctx.job_id, "first_broken_audit_id": broken_id})
