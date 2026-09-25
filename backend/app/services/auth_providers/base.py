"""Pluggable credential verification. Everything after "credentials are valid" is shared."""

from __future__ import annotations

from typing import Protocol

from app.models.user import AppUser


class AuthProvider(Protocol):
    source: str  # value stored in app_user.auth_source

    def authenticate(self, username: str, password: str) -> AppUser | None:
        """Return the active user if the credentials are valid, otherwise None."""
        ...
