"""Authentication request/response models."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import UtcDatetime


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9._@\-]+$")
    password: str = Field(min_length=1, max_length=256)  # never stripped or logged

    @field_validator("username", mode="before")
    @classmethod
    def _normalise_username(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value


class ModuleAccess(BaseModel):
    code: str
    name: str
    is_enabled: bool
    roles: list[str]
    permissions: list[str]


class UserProfile(BaseModel):
    id: int
    username: str
    display_name: str
    email: str | None = None
    auth_source: str
    last_login_at: UtcDatetime | None = None
    modules: list[ModuleAccess]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"  # noqa: S105 - OAuth token type, not a secret
    expires_in: int = Field(description="Access token lifetime in seconds")
    expires_at: UtcDatetime
    user: UserProfile
