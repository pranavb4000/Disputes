"""Home page data. Dispute figures are placeholders until the UPI module (Phase 1a) is built."""

from __future__ import annotations

from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import AppUser
from app.repositories.audit_repository import AuditRepository
from app.repositories.user_repository import ModuleRepository, UserRepository
from app.schemas.home import ActivityItem, DisputeStatusCount, HomeSummary, ModuleCard, ModuleSummary
from app.services.access_service import AccessService


class HomeService:
    def __init__(self, settings: Settings, db: Session, redis: Redis) -> None:
        self._modules = ModuleRepository(db)
        self._audit = AuditRepository(db)
        self._access = AccessService(settings, redis, UserRepository(db), self._modules)

    def summary(self, user: AppUser) -> HomeSummary:
        roles = self._access.roles_by_module(user.id)
        cards = [
            ModuleCard(
                code=m.code,
                name=m.name,
                description=m.description,
                is_enabled=m.is_enabled,
                has_access=bool(roles.get(m.code)),
                roles=sorted(roles.get(m.code, set())),
            )
            for m in self._modules.list_all()
        ]
        activity = [
            ActivityItem(occurred_at=a.occurred_at, action=a.action, outcome=a.outcome, ip_address=a.ip_address)
            for a in self._audit.recent_for_user(user.id, limit=10)
        ]
        # The most recent LOGIN row is the current session; the one before it is the previous login.
        logins = [a for a in activity if a.action == "LOGIN" and a.outcome == "SUCCESS"]
        previous_login = logins[1].occurred_at if len(logins) > 1 else None
        return HomeSummary(
            greeting_name=user.display_name,
            last_login_at=previous_login,
            modules=cards,
            recent_activity=activity,
            notice="Scaffold build: dispute figures are sample placeholders until Phase 1a.",
        )

    def module_summary(self, module_code: str) -> ModuleSummary:
        # Placeholder numbers so the dashboard widgets can be wired end to end.
        return ModuleSummary(
            module_code=module_code.upper(),
            open_disputes=0,
            pending_approval=0,
            breached_sla=0,
            by_status=[
                DisputeStatusCount(status="RECEIVED", count=0),
                DisputeStatusCount(status="UNDER_REVIEW", count=0),
                DisputeStatusCount(status="PENDING_APPROVAL", count=0),
                DisputeStatusCount(status="CLOSED", count=0),
            ],
        )
