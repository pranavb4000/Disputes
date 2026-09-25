"""Home page models."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import UtcDatetime


class ActivityItem(BaseModel):
    occurred_at: UtcDatetime
    action: str
    outcome: str
    ip_address: str | None = None


class ModuleCard(BaseModel):
    code: str
    name: str
    description: str | None = None
    is_enabled: bool
    has_access: bool
    roles: list[str]


class HomeSummary(BaseModel):
    greeting_name: str
    last_login_at: UtcDatetime | None = None
    modules: list[ModuleCard]
    recent_activity: list[ActivityItem]
    notice: str | None = None


class DisputeStatusCount(BaseModel):
    status: str
    count: int


class ModuleSummary(BaseModel):
    module_code: str
    open_disputes: int
    pending_approval: int
    breached_sla: int
    by_status: list[DisputeStatusCount]
    is_placeholder: bool = True
