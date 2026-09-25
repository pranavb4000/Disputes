"""JWT (HS512) and password hashing primitives (TECH_STACK.md §8).

- Access tokens: signed JWTs (HS512). Signed is NOT encrypted, so claims hold no secrets.
- Refresh tokens: opaque random strings; only their SHA-256 hash is ever stored (see token_service).
- Passwords: used only by the dev-only local login. hashlib.scrypt from the standard library.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.core.config import Settings
from app.core.exceptions import TokenError

# A JWT claim value, not a secret.
ACCESS_TOKEN_TYPE = "access"  # noqa: S105  # nosec B105


@dataclass(frozen=True)
class AccessTokenClaims:
    user_id: int
    username: str
    jti: str
    issued_at: datetime
    expires_at: datetime


def create_access_token(
    settings: Settings, *, user_id: int, username: str, roles: dict[str, list[str]], now: datetime | None = None
) -> tuple[str, AccessTokenClaims]:
    issued = now or datetime.now(UTC)
    expires = issued + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    jti = uuid.uuid4().hex
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "iss": settings.jwt_issuer,
        "iat": int(issued.timestamp()),
        "exp": int(expires.timestamp()),
        "jti": jti,
        "typ": ACCESS_TOKEN_TYPE,
        # UI hints only. The server re-checks permissions from the database on every request.
        "roles": roles,
    }
    token = jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm)
    return token, AccessTokenClaims(user_id, username, jti, issued, expires)


def decode_access_token(settings: Settings, token: str) -> AccessTokenClaims:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],  # pin the algorithm: rejects "none" and HS256 downgrades
            issuer=settings.jwt_issuer,
            options={"require": ["sub", "iat", "exp", "jti", "iss"]},
        )
    except jwt.PyJWTError as exc:
        raise TokenError() from exc
    if payload.get("typ") != ACCESS_TOKEN_TYPE:
        raise TokenError()
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise TokenError() from exc
    return AccessTokenClaims(
        user_id=user_id,
        username=str(payload.get("username", "")),
        jti=str(payload["jti"]),
        issued_at=datetime.fromtimestamp(payload["iat"], UTC),
        expires_at=datetime.fromtimestamp(payload["exp"], UTC),
    )


# --- Refresh tokens -----------------------------------------------------------------------------


def new_refresh_token() -> str:
    return secrets.token_urlsafe(32)  # 256 bits


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# --- Passwords (dev-only local login) --------------------------------------------------------------

_SCRYPT_N, _SCRYPT_R, _SCRYPT_P, _SCRYPT_LEN = 2**14, 8, 1, 64


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=_SCRYPT_LEN)
    b64 = base64.b64encode
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${b64(salt).decode()}${b64(digest).decode()}"


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        # Burn comparable CPU time so unknown users are not detectable by timing.
        hashlib.scrypt(b"x", salt=b"0" * 16, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=_SCRYPT_LEN)
        return False
    try:
        scheme, n, r, p, salt_b64, digest_b64 = stored_hash.split("$")
        if scheme != "scrypt":
            return False
        expected = base64.b64decode(digest_b64)
        actual = hashlib.scrypt(
            password.encode(), salt=base64.b64decode(salt_b64), n=int(n), r=int(r), p=int(p), dklen=len(expected)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)
