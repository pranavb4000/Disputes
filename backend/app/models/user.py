"""Users, product modules and module-scoped role assignments."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, Identity, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class AppModule(Base):
    """A product module such as UPI, IMPS, AEPS or ETOLL."""

    __tablename__ = "app_module"

    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(400))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class AppUser(TimestampMixin, Base):
    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)  # ACTIVE | DISABLED
    auth_source: Mapped[str] = mapped_column(String(10), default="LOCAL", nullable=False)  # LOCAL | LDAP
    password_hash: Mapped[str | None] = mapped_column(String(255))  # LOCAL (dev) only
    last_login_at: Mapped[datetime | None] = mapped_column(TIMESTAMP())

    roles: Mapped[list[UserModuleRole]] = relationship(back_populates="user", lazy="selectin")

    @property
    def is_active(self) -> bool:
        return self.status == "ACTIVE"


class UserModuleRole(Base):
    __tablename__ = "user_module_role"
    __table_args__ = (UniqueConstraint("user_id", "module_code", "role_code"),)

    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id"), nullable=False, index=True)
    module_code: Mapped[str] = mapped_column(ForeignKey("app_module.code"), nullable=False)
    role_code: Mapped[str] = mapped_column(String(20), nullable=False)  # ADMIN | MAKER | CHECKER

    user: Mapped[AppUser] = relationship(back_populates="roles")
