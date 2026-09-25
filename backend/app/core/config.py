"""Application settings, loaded from environment variables / .env files (TECH_STACK.md §18).

Precedence (highest first): real environment variables > backend/.env > ../.env (repo root).
The repo-root .env is shared with docker-compose, so one file configures both.
"""

from __future__ import annotations

import base64
import binascii
import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[2]

Environment = Literal["development", "test", "staging", "production"]


def _decode_key(value: SecretStr, name: str, expected_len: int) -> bytes:
    try:
        raw = base64.b64decode(value.get_secret_value(), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"{name} must be base64-encoded") from exc
    if len(raw) != expected_len:
        raise ValueError(f"{name} must decode to exactly {expected_len} bytes (got {len(raw)})")
    return raw


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_BACKEND_DIR.parent / ".env", _BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ---------------------------------------------------------------
    app_env: Environment = "development"
    app_name: str = "Dispute Management System"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    docs_enabled: bool = True  # OpenAPI /docs; forced off in production

    # Browser origin that serves the Flutter app (Nginx). Used for the CSRF Origin check.
    public_origin: str = "http://localhost:8080"
    # Extra origins allowed for CORS (development only, e.g. `flutter run` on :5000). JSON list.
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)

    # --- Oracle ------------------------------------------------------------------------
    database_host: str = "localhost"
    database_port: int = 1521
    database_service: str = "XEPDB1"
    database_user: str = "dms_app"
    database_password: SecretStr = SecretStr("")
    db_pool_size: int = 5
    db_max_overflow: int = 5
    db_echo: bool = False

    # --- Redis -------------------------------------------------------------------------
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: SecretStr | None = None
    redis_db: int = 0
    redis_ssl: bool = False
    redis_key_prefix: str = "dms"

    # --- Authentication ------------------------------------------------------------------
    auth_provider: Literal["local", "ldap"] = "local"
    jwt_secret: SecretStr = SecretStr("")
    jwt_algorithm: Literal["HS512"] = "HS512"
    jwt_issuer: str = "dms"
    jwt_access_token_expire_minutes: int = 15
    refresh_token_idle_minutes: int = 30
    refresh_token_absolute_hours: int = 10
    refresh_reuse_grace_seconds: int = 10
    refresh_cookie_name: str = "dms_rt"
    cookie_secure: bool = True
    client_header_name: str = "X-DMS-Client"
    login_max_failures: int = 5
    login_lockout_minutes: int = 15
    login_ip_limit_per_minute: int = 30
    permission_cache_seconds: int = 60

    # LDAP (Phase 2) -- only read when AUTH_PROVIDER=ldap
    ldap_url: str = ""
    ldap_bind_dn: str = ""
    ldap_bind_password: SecretStr = SecretStr("")
    ldap_user_search_base: str = ""
    ldap_user_filter: str = "(sAMAccountName={username})"
    ldap_timeout_seconds: int = 10

    # --- Encryption (AES-256-GCM) --------------------------------------------------------
    aes_encryption_key: SecretStr = SecretStr("")  # base64, 32 bytes
    aes_key_version: int = 1
    aes_previous_keys: dict[int, SecretStr] = Field(default_factory=dict)  # {version: base64 key}
    blind_index_key: SecretStr = SecretStr("")  # base64, 32 bytes (HMAC-SHA256)

    # --- File storage ----------------------------------------------------------------------
    storage_backend: Literal["local", "s3"] = "local"
    storage_local_path: str = str(_BACKEND_DIR / ".data" / "files")
    s3_bucket: str = ""
    s3_kms_key_id: str = ""
    aws_region: str = "ap-south-1"

    # --- Worker ----------------------------------------------------------------------------
    worker_queues: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["ingest", "light"])
    worker_poll_seconds: int = 5
    worker_lease_seconds: int = 300
    worker_scheduler_interval_seconds: int = 30

    # --- Dev-only seed users (scripts/seed_dev.py) --------------------------------------------
    dev_user_password: SecretStr = SecretStr("")
    dev_checker_password: SecretStr = SecretStr("")

    # ------------------------------------------------------------------------------------------
    @field_validator("cors_origins", "worker_queues", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        """Accept either a JSON list or a comma-separated string."""
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                return json.loads(text)
            return [item.strip() for item in text.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def _validate_security(self) -> Settings:
        if self.app_env in ("staging", "production"):
            if self.auth_provider == "local":
                raise ValueError("AUTH_PROVIDER=local is for development only; use ldap in staging/production")
            if not self.cookie_secure:
                raise ValueError("COOKIE_SECURE must be true outside development")
            self.docs_enabled = self.docs_enabled and self.app_env != "production"
        secret = self.jwt_secret.get_secret_value()
        if len(secret.encode()) < 64:
            raise ValueError("JWT_SECRET must be at least 64 bytes for HS512 (generate with tools/init_env.py)")
        _decode_key(self.aes_encryption_key, "AES_ENCRYPTION_KEY", 32)
        _decode_key(self.blind_index_key, "BLIND_INDEX_KEY", 32)
        for version, key in self.aes_previous_keys.items():
            _decode_key(key, f"AES_PREVIOUS_KEYS[{version}]", 32)
        if self.storage_backend == "s3" and not self.s3_bucket:
            raise ValueError("S3_BUCKET is required when STORAGE_BACKEND=s3")
        return self

    # Convenience accessors --------------------------------------------------------------------
    @property
    def is_development(self) -> bool:
        return self.app_env in ("development", "test")

    @property
    def aes_keys(self) -> dict[int, bytes]:
        keys = {v: _decode_key(k, "AES key", 32) for v, k in self.aes_previous_keys.items()}
        keys[self.aes_key_version] = _decode_key(self.aes_encryption_key, "AES_ENCRYPTION_KEY", 32)
        return keys

    @property
    def blind_index_key_bytes(self) -> bytes:
        return _decode_key(self.blind_index_key, "BLIND_INDEX_KEY", 32)

    @property
    def allowed_origins(self) -> set[str]:
        return {self.public_origin.rstrip("/"), *(o.rstrip("/") for o in self.cors_origins)}


@lru_cache
def get_settings() -> Settings:
    return Settings()
