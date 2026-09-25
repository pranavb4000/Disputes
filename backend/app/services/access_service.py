"""Module-scoped authorisation (ARCHITECTURE.md §9.3).

Roles come from Oracle (source of truth) and are cached in Redis briefly so every request can
re-check permissions cheaply. Call `invalidate(user_id)` whenever a user's roles change.
"""

from __future__ import annotations

import json
import logging

from redis import Redis
from redis.exceptions import RedisError

from app.cache.redis import key
from app.core.config import Settings
from app.core.exceptions import PermissionDeniedError
from app.core.permissions import permissions_for
from app.repositories.user_repository import ModuleRepository, UserRepository
from app.schemas.auth import ModuleAccess

logger = logging.getLogger(__name__)


class AccessService:
    def __init__(self, settings: Settings, redis: Redis, users: UserRepository, modules: ModuleRepository) -> None:
        self._s = settings
        self._r = redis
        self._users = users
        self._modules = modules

    def roles_by_module(self, user_id: int) -> dict[str, set[str]]:
        cache_key = key("perm", user_id)
        try:
            cached = self._r.get(cache_key)
            if cached is not None:
                return {m: set(r) for m, r in json.loads(str(cached)).items()}
        except RedisError:
            logger.warning("Permission cache unavailable; reading roles from database")
        roles = self._users.roles_by_module(user_id)
        try:
            payload = json.dumps({m: sorted(r) for m, r in roles.items()})
            self._r.set(cache_key, payload, ex=self._s.permission_cache_seconds)
        except RedisError:
            pass
        return roles

    def invalidate(self, user_id: int) -> None:
        self._r.delete(key("perm", user_id))

    def module_access(self, user_id: int) -> list[ModuleAccess]:
        roles = self.roles_by_module(user_id)
        result = []
        for module in self._modules.list_all():
            module_roles = roles.get(module.code, set())
            if not module_roles:
                continue
            result.append(
                ModuleAccess(
                    code=module.code,
                    name=module.name,
                    is_enabled=module.is_enabled,
                    roles=sorted(module_roles),
                    permissions=sorted(permissions_for(module_roles)),
                )
            )
        return result

    def require(self, user_id: int, module_code: str, permission: str) -> None:
        module = self._modules.get(module_code.upper())
        if module is None or not module.is_enabled:
            raise PermissionDeniedError("This module is not available")
        granted = permissions_for(self.roles_by_module(user_id).get(module.code, set()))
        if permission not in granted:
            raise PermissionDeniedError()
