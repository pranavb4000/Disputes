"""Import every model here so Alembic and metadata.create_all() see all tables."""

from app.models.audit import AuditChain, AuditLog
from app.models.base import Base
from app.models.job import Job, JobSchedule
from app.models.user import AppModule, AppUser, UserModuleRole

__all__ = ["AppModule", "AppUser", "AuditChain", "AuditLog", "Base", "Job", "JobSchedule", "UserModuleRole"]
