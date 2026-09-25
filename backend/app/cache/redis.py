"""Redis client (TECH_STACK.md §7). Redis is never the source of truth for business data."""

from __future__ import annotations

from functools import lru_cache

from redis import Redis

from app.core.config import Settings, get_settings


def create_redis(settings: Settings, *, socket_timeout: float | None = 5.0) -> Redis:
    return Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password.get_secret_value() if settings.redis_password else None,
        ssl=settings.redis_ssl,
        decode_responses=True,
        socket_timeout=socket_timeout,
        socket_connect_timeout=5.0,
        health_check_interval=30,
    )


@lru_cache
def get_redis() -> Redis:
    return create_redis(get_settings())


def key(*parts: object) -> str:
    """Namespaced key, e.g. key("rt", "abc") -> "dms:rt:abc"."""
    return ":".join([get_settings().redis_key_prefix, *(str(p) for p in parts)])
