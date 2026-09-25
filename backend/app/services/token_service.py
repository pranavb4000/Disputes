"""Access / refresh token lifecycle (ARCHITECTURE.md §9.2).

Refresh tokens are opaque random strings stored in Redis by SHA-256 hash:
  {prefix}:rt:{hash}        -> JSON {user_id, family, abs_exp}   TTL = idle timeout
  {prefix}:rtfam:{family}   -> "1"                               TTL = absolute session limit
  {prefix}:rtused:{hash}    -> JSON {family, used_at}            TTL = absolute session limit
  {prefix}:deny:{jti}       -> "1"                               TTL = remaining access-token life

Every refresh rotates the token. Presenting an already-used token (outside a short grace window
for parallel browser tabs) is treated as theft: the whole token family is revoked.
"""

from __future__ import annotations

import json
import logging
import secrets
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from redis import Redis

from app.cache.redis import key
from app.core.config import Settings
from app.core.exceptions import TokenError
from app.core.security import AccessTokenClaims, create_access_token, decode_access_token, hash_token, new_refresh_token

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IssuedTokens:
    access_token: str
    access_claims: AccessTokenClaims
    refresh_token: str
    refresh_max_age: int  # seconds, for the cookie


class TokenService:
    def __init__(self, settings: Settings, redis: Redis) -> None:
        self._s = settings
        self._r = redis

    # --- issue ---------------------------------------------------------------------------------
    def issue(
        self,
        *,
        user_id: int,
        username: str,
        roles: dict[str, list[str]],
        family: str | None = None,
        absolute_expiry: int | None = None,
    ) -> IssuedTokens:
        access, claims = create_access_token(self._s, user_id=user_id, username=username, roles=roles)
        now = int(time.time())
        family = family or secrets.token_hex(16)
        abs_exp = absolute_expiry or now + self._s.refresh_token_absolute_hours * 3600
        idle_ttl = self._s.refresh_token_idle_minutes * 60
        ttl = max(1, min(idle_ttl, abs_exp - now))
        refresh = new_refresh_token()
        record = json.dumps({"user_id": user_id, "family": family, "abs_exp": abs_exp})
        self._r.set(key("rt", hash_token(refresh)), record, ex=ttl)
        if not self._r.exists(key("rtfam", family)):
            self._r.set(key("rtfam", family), "1", ex=max(1, abs_exp - now))
        return IssuedTokens(access, claims, refresh, ttl)

    # --- refresh -------------------------------------------------------------------------------
    def consume_refresh(self, refresh_token: str) -> tuple[int, str, int]:
        """Validate and invalidate a refresh token. Returns (user_id, family, absolute_expiry)."""
        token_hash = hash_token(refresh_token)
        raw = self._r.getdel(key("rt", token_hash))
        now = int(time.time())
        if raw is None:
            used_raw = self._r.get(key("rtused", token_hash))
            if used_raw:
                used = json.loads(used_raw)
                if now - int(used["used_at"]) > self._s.refresh_reuse_grace_seconds:
                    self.revoke_family(used["family"])
                    logger.warning(
                        "Refresh token reuse detected; session family revoked", extra={"family": used["family"]}
                    )
            raise TokenError()
        record = json.loads(str(raw))
        family, abs_exp = str(record["family"]), int(record["abs_exp"])
        if abs_exp <= now or not self._r.exists(key("rtfam", family)):
            raise TokenError()
        self._r.set(key("rtused", token_hash), json.dumps({"family": family, "used_at": now}), ex=max(1, abs_exp - now))
        return int(record["user_id"]), family, abs_exp

    def revoke_family(self, family: str) -> None:
        self._r.delete(key("rtfam", family))

    def revoke_refresh(self, refresh_token: str) -> None:
        raw = self._r.getdel(key("rt", hash_token(refresh_token)))
        if raw:
            self.revoke_family(str(json.loads(str(raw))["family"]))

    # --- access tokens ---------------------------------------------------------------------------
    def validate_access(self, token: str) -> AccessTokenClaims:
        claims = decode_access_token(self._s, token)
        if self._r.exists(key("deny", claims.jti)):
            raise TokenError()
        return claims

    def deny_access(self, claims: AccessTokenClaims) -> None:
        remaining = int((claims.expires_at - datetime.now(UTC)).total_seconds())
        if remaining > 0:
            self._r.set(key("deny", claims.jti), "1", ex=remaining)
