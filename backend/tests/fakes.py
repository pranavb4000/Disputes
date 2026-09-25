"""Minimal in-memory Redis stand-in for unit/API tests (only the commands the app uses)."""

from __future__ import annotations

import time
from typing import Any


class FakeRedis:
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._expiry: dict[str, float] = {}

    def _purge(self, key: str) -> None:
        exp = self._expiry.get(key)
        if exp is not None and exp <= time.time():
            self._data.pop(key, None)
            self._expiry.pop(key, None)

    def get(self, key: str) -> Any:
        self._purge(key)
        value = self._data.get(key)
        return None if isinstance(value, list) else value

    def set(self, key: str, value: Any, ex: int | None = None, nx: bool = False) -> bool | None:
        self._purge(key)
        if nx and key in self._data:
            return None
        self._data[key] = str(value)
        if ex is not None:
            self._expiry[key] = time.time() + ex
        else:
            self._expiry.pop(key, None)
        return True

    def getdel(self, key: str) -> Any:
        value = self.get(key)
        self.delete(key)
        return value

    def delete(self, *keys: str) -> int:
        removed = 0
        for key in keys:
            removed += int(self._data.pop(key, None) is not None)
            self._expiry.pop(key, None)
        return removed

    def exists(self, *keys: str) -> int:
        count = 0
        for key in keys:
            self._purge(key)
            count += int(key in self._data)
        return count

    def incr(self, key: str) -> int:
        self._purge(key)
        value = int(self._data.get(key, 0)) + 1
        self._data[key] = str(value)
        return value

    def expire(self, key: str, seconds: int) -> bool:
        if key in self._data:
            self._expiry[key] = time.time() + seconds
            return True
        return False

    def ttl(self, key: str) -> int:
        self._purge(key)
        if key not in self._data:
            return -2
        exp = self._expiry.get(key)
        return -1 if exp is None else int(exp - time.time())

    def lpush(self, key: str, *values: Any) -> int:
        lst = self._data.setdefault(key, [])
        for v in values:
            lst.insert(0, str(v))
        return len(lst)

    def ltrim(self, key: str, start: int, end: int) -> bool:
        if key in self._data:
            self._data[key] = self._data[key][start : end + 1]
        return True

    def brpop(self, keys: list[str], timeout: int = 0) -> tuple[str, str] | None:
        for key in keys:
            lst = self._data.get(key)
            if lst:
                return key, lst.pop()
        return None

    def ping(self) -> bool:
        return True

    # test helper
    def expire_now(self, key: str) -> None:
        self._expiry[key] = time.time() - 1
