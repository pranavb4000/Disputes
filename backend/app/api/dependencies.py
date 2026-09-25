"""Shared FastAPI dependencies: settings, DB session, Redis, current user, permission checks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Path, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from sqlalchemy.orm import Session

from app.cache.redis import get_redis
from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError, CsrfError, TokenError
from app.core.logging import user_id_var
from app.core.security import AccessTokenClaims
from app.db.session import get_db
from app.models.user import AppUser
from app.repositories.user_repository import ModuleRepository, UserRepository
from app.services.access_service import AccessService
from app.services.audit_service import AuditContext
from app.services.auth_service import AuthService
from app.services.home_service import HomeService

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbDep = Annotated[Session, Depends(get_db)]
RedisDep = Annotated[Redis, Depends(get_redis)]

_bearer = HTTPBearer(auto_error=False, description="Access token from /api/v1/auth/login")


def get_auth_service(settings: SettingsDep, db: DbDep, redis: RedisDep) -> AuthService:
    return AuthService(settings, db, redis)


def get_home_service(settings: SettingsDep, db: DbDep, redis: RedisDep) -> HomeService:
    return HomeService(settings, db, redis)


def get_access_service(settings: SettingsDep, db: DbDep, redis: RedisDep) -> AccessService:
    return AccessService(settings, redis, UserRepository(db), ModuleRepository(db))


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
HomeServiceDep = Annotated[HomeService, Depends(get_home_service)]
AccessServiceDep = Annotated[AccessService, Depends(get_access_service)]


def audit_context(request: Request) -> AuditContext:
    return AuditContext(
        ip_address=request.client.host if request.client else None,
        request_id=getattr(request.state, "request_id", None),
    )


AuditContextDep = Annotated[AuditContext, Depends(audit_context)]


def optional_access_claims(
    auth: AuthServiceDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AccessTokenClaims | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        return auth.validate_access_token(credentials.credentials)
    except TokenError:
        return None


def require_access_claims(
    request: Request,
    auth: AuthServiceDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AccessTokenClaims:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError()
    claims = auth.validate_access_token(credentials.credentials)
    request.state.user_id = str(claims.user_id)  # picked up by the request log line
    user_id_var.set(str(claims.user_id))
    return claims


ClaimsDep = Annotated[AccessTokenClaims, Depends(require_access_claims)]


@dataclass(frozen=True)
class CurrentUser:
    user: AppUser
    claims: AccessTokenClaims


def get_current_user(claims: ClaimsDep, db: DbDep) -> CurrentUser:
    user = UserRepository(db).get_by_id(claims.user_id)
    if user is None or not user.is_active:
        raise TokenError()
    return CurrentUser(user=user, claims=claims)


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def require_permission(permission: str) -> Callable[..., CurrentUser]:
    """Dependency factory for routes shaped /api/v1/{module_code}/... ."""

    def checker(
        current: CurrentUserDep,
        access: AccessServiceDep,
        module_code: Annotated[str, Path(pattern=r"^[A-Za-z]{2,20}$")],
    ) -> CurrentUser:
        access.require(current.user.id, module_code, permission)
        return current

    return checker


def verify_browser_request(request: Request, settings: SettingsDep) -> None:
    """CSRF defence for the cookie-authenticated endpoints (/auth/refresh, /auth/logout)."""
    if request.headers.get(settings.client_header_name) != "web":
        raise CsrfError()
    origin = request.headers.get("Origin")
    if origin is not None and origin.rstrip("/") not in settings.allowed_origins:
        raise CsrfError()
