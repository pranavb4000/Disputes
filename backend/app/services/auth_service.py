"""Login, refresh and logout workflows (ARCHITECTURE.md §9.1-9.2)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from redis import Redis
from sqlalchemy.orm import Session

from app.cache.redis import key
from app.core.config import Settings
from app.core.exceptions import InvalidCredentialsError, RateLimitedError, TokenError
from app.core.security import AccessTokenClaims
from app.models.user import AppUser
from app.repositories.user_repository import ModuleRepository, UserRepository
from app.schemas.auth import TokenResponse, UserProfile
from app.services.access_service import AccessService
from app.services.audit_service import AuditContext, AuditService
from app.services.auth_providers import AuthProvider, LdapAuthProvider, LocalAuthProvider
from app.services.token_service import IssuedTokens, TokenService
from app.utils.time import utcnow

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthResult:
    body: TokenResponse
    refresh_token: str
    refresh_max_age: int


class AuthService:
    def __init__(self, settings: Settings, db: Session, redis: Redis) -> None:
        self._s = settings
        self._db = db
        self._r = redis
        self._users = UserRepository(db)
        self._access = AccessService(settings, redis, self._users, ModuleRepository(db))
        self._tokens = TokenService(settings, redis)
        self._audit = AuditService(db)

    # --- helpers --------------------------------------------------------------------------------
    def _provider(self) -> AuthProvider:
        if self._s.auth_provider == "ldap":
            return LdapAuthProvider(self._s, self._users)
        return LocalAuthProvider(self._users)

    def _check_rate_limits(self, username: str, ip: str | None) -> None:
        if ip:
            ip_key = key("loginip", ip)
            attempts = self._r.incr(ip_key)
            if attempts == 1:
                self._r.expire(ip_key, 60)
            if int(attempts) > self._s.login_ip_limit_per_minute:
                raise RateLimitedError()
        fails = self._r.get(key("loginfail", username))
        if fails is not None and int(fails) >= self._s.login_max_failures:
            raise RateLimitedError(
                "Account temporarily locked after repeated failed logins. Try again later.", error_code="ACCOUNT_LOCKED"
            )

    def _register_failure(self, username: str) -> None:
        fail_key = key("loginfail", username)
        count = self._r.incr(fail_key)
        if count == 1:
            self._r.expire(fail_key, self._s.login_lockout_minutes * 60)

    def build_profile(self, user: AppUser) -> UserProfile:
        return UserProfile(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            email=user.email,
            auth_source=user.auth_source,
            last_login_at=user.last_login_at,
            modules=self._access.module_access(user.id),
        )

    def _token_response(self, user: AppUser, issued: IssuedTokens) -> TokenResponse:
        return TokenResponse(
            access_token=issued.access_token,
            expires_in=self._s.jwt_access_token_expire_minutes * 60,
            expires_at=issued.access_claims.expires_at,
            user=self.build_profile(user),
        )

    def _issue(self, user: AppUser, *, family: str | None = None, absolute_expiry: int | None = None) -> IssuedTokens:
        roles = {m: sorted(r) for m, r in self._access.roles_by_module(user.id).items()}
        return self._tokens.issue(
            user_id=user.id, username=user.username, roles=roles, family=family, absolute_expiry=absolute_expiry
        )

    # --- use cases ------------------------------------------------------------------------------
    def login(self, username: str, password: str, ctx: AuditContext) -> AuthResult:
        self._check_rate_limits(username, ctx.ip_address)
        user = self._provider().authenticate(username, password)
        if user is None:
            self._register_failure(username)
            self._audit.record(
                "LOGIN",
                outcome="FAILURE",
                actor_username=username,
                context=ctx,
                details={"reason": "invalid_credentials"},
            )
            self._db.commit()
            raise InvalidCredentialsError()

        self._r.delete(key("loginfail", username))
        previous_login = user.last_login_at
        issued = self._issue(user)
        self._users.set_last_login(user.id, utcnow())
        self._audit.record("LOGIN", actor_user_id=user.id, actor_username=user.username, context=ctx)
        self._db.commit()
        body = self._token_response(user, issued)
        body.user.last_login_at = previous_login  # show the *previous* login on the home page
        return AuthResult(body, issued.refresh_token, issued.refresh_max_age)

    def refresh(self, refresh_token: str | None, ctx: AuditContext) -> AuthResult:
        if not refresh_token:
            raise TokenError()
        user_id, family, abs_exp = self._tokens.consume_refresh(refresh_token)
        user = self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            self._tokens.revoke_family(family)
            raise TokenError()
        issued = self._issue(user, family=family, absolute_expiry=abs_exp)
        return AuthResult(self._token_response(user, issued), issued.refresh_token, issued.refresh_max_age)

    def logout(self, refresh_token: str | None, access_claims: AccessTokenClaims | None, ctx: AuditContext) -> None:
        if refresh_token:
            self._tokens.revoke_refresh(refresh_token)
        if access_claims:
            self._tokens.deny_access(access_claims)
            self._audit.record(
                "LOGOUT", actor_user_id=access_claims.user_id, actor_username=access_claims.username, context=ctx
            )
            self._db.commit()

    def validate_access_token(self, token: str) -> AccessTokenClaims:
        return self._tokens.validate_access(token)
