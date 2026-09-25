"""Data access for users, modules and module roles. No business rules here."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.user import AppModule, AppUser, UserModuleRole


class UserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, user_id: int) -> AppUser | None:
        return self._db.get(AppUser, user_id)

    def get_by_username(self, username: str) -> AppUser | None:
        stmt = select(AppUser).where(func.lower(AppUser.username) == username.lower())
        return self._db.execute(stmt).scalar_one_or_none()

    def add(self, user: AppUser) -> AppUser:
        self._db.add(user)
        self._db.flush()
        return user

    def set_last_login(self, user_id: int, when: datetime) -> None:
        self._db.execute(update(AppUser).where(AppUser.id == user_id).values(last_login_at=when))

    def roles_by_module(self, user_id: int) -> dict[str, set[str]]:
        stmt = select(UserModuleRole.module_code, UserModuleRole.role_code).where(UserModuleRole.user_id == user_id)
        result: dict[str, set[str]] = {}
        for module_code, role_code in self._db.execute(stmt):
            result.setdefault(module_code, set()).add(role_code)
        return result

    def add_role(self, user_id: int, module_code: str, role_code: str) -> None:
        exists = self._db.execute(
            select(UserModuleRole.id).where(
                UserModuleRole.user_id == user_id,
                UserModuleRole.module_code == module_code,
                UserModuleRole.role_code == role_code,
            )
        ).first()
        if not exists:
            self._db.add(UserModuleRole(user_id=user_id, module_code=module_code, role_code=role_code))


class ModuleRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_all(self) -> list[AppModule]:
        stmt = select(AppModule).order_by(AppModule.display_order, AppModule.code)
        return list(self._db.execute(stmt).scalars())

    def get(self, code: str) -> AppModule | None:
        return self._db.get(AppModule, code)

    def upsert(self, module: AppModule) -> None:
        self._db.merge(module)
