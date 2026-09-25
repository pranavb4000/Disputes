"""Liveness and readiness probes (used by Docker/ECS health checks)."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app import __version__
from app.api.dependencies import DbDep, RedisDep, SettingsDep
from app.core.responses import ApiResponse, error_body, ok
from app.schemas.system import HealthStatus, ReadinessStatus

router = APIRouter(prefix="/health", tags=["Health"])
logger = logging.getLogger(__name__)


@router.get("", response_model=ApiResponse[HealthStatus], summary="Liveness")
def liveness(settings: SettingsDep) -> ApiResponse[HealthStatus]:
    return ok(HealthStatus(status="ok", version=__version__, environment=settings.app_env))


@router.get(
    "/ready",
    response_model=ApiResponse[ReadinessStatus],
    summary="Readiness (Oracle + Redis)",
    responses={503: {"description": "A dependency is down"}},
)
def readiness(db: DbDep, redis: RedisDep) -> ApiResponse[ReadinessStatus] | JSONResponse:
    checks: dict[str, str] = {}
    try:
        db.execute(text("SELECT 1 FROM DUAL")).scalar_one()
        checks["oracle"] = "ok"
    except Exception as exc:  # noqa: BLE001 - report, never raise, from a probe
        logger.warning("Oracle readiness check failed", extra={"error_type": type(exc).__name__})
        checks["oracle"] = "down"
    try:
        redis.ping()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis readiness check failed", extra={"error_type": type(exc).__name__})
        checks["redis"] = "down"
    if all(v == "ok" for v in checks.values()):
        return ok(ReadinessStatus(status="ok", checks=checks))
    return JSONResponse(
        error_body("Not ready", "SERVICE_UNAVAILABLE", {"status": "down", "checks": checks}), status_code=503
    )
