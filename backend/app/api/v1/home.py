"""Home page endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import CurrentUser, CurrentUserDep, HomeServiceDep, require_permission
from app.core.permissions import Permission
from app.core.responses import ApiResponse, ok
from app.schemas.home import HomeSummary, ModuleSummary

router = APIRouter(tags=["Home"])


@router.get(
    "/home",
    response_model=ApiResponse[HomeSummary],
    summary="Home page summary",
    description="Greeting, module cards and the user's recent activity.",
    responses={401: {"description": "Not authenticated"}},
)
def home(current: CurrentUserDep, service: HomeServiceDep) -> ApiResponse[HomeSummary]:
    return ok(service.summary(current.user))


@router.get(
    "/{module_code}/summary",
    response_model=ApiResponse[ModuleSummary],
    summary="Module dashboard summary",
    description="Dispute counts for one module. Requires dispute.view on that module. "
    "Returns placeholder zeros until Phase 1a.",
    responses={401: {"description": "Not authenticated"}, 403: {"description": "No access to this module"}},
)
def module_summary(
    module_code: str,
    _: Annotated[CurrentUser, Depends(require_permission(Permission.DISPUTE_VIEW))],
    service: HomeServiceDep,
) -> ApiResponse[ModuleSummary]:
    return ok(service.module_summary(module_code))
