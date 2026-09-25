"""File storage abstraction: S3 in AWS, a local folder in development (ARCHITECTURE.md §8)."""

from __future__ import annotations

import re
from typing import BinaryIO, Protocol

_SAFE_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9/_\-.]{0,511}$")


def validate_key(object_key: str) -> str:
    if not _SAFE_KEY.match(object_key) or ".." in object_key or "//" in object_key:
        raise ValueError("Invalid storage key")
    return object_key


class FileStorage(Protocol):
    def put(self, object_key: str, data: BinaryIO, content_type: str = "application/octet-stream") -> None: ...

    def open(self, object_key: str) -> BinaryIO: ...

    def exists(self, object_key: str) -> bool: ...

    def delete(self, object_key: str) -> None: ...

    def scan_status(self, object_key: str) -> str | None:
        """Malware scan result: NO_THREATS_FOUND, THREATS_FOUND, ... or None if not scanned yet."""
        ...
