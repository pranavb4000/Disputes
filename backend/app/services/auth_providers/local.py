"""DEVELOPMENT-ONLY local login (password hash in app_user). Refused in staging/production by config."""

from __future__ import annotations

from app.core.security import verify_password
from app.models.user import AppUser
from app.repositories.user_repository import UserRepository


class LocalAuthProvider:
    source = "LOCAL"

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def authenticate(self, username: str, password: str) -> AppUser | None:
        user = self._users.get_by_username(username)
        valid_user = user is not None and user.auth_source == self.source and user.is_active
        stored = user.password_hash if (user is not None and valid_user) else None
        # verify_password runs even for unknown users (constant-ish time).
        if verify_password(password, stored) and valid_user:
            return user
        return None
