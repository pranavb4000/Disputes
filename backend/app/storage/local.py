"""Local-folder storage for development and tests. Never used in AWS."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import BinaryIO

from app.storage.base import validate_key


class LocalFileStorage:
    def __init__(self, root: str | Path) -> None:
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, object_key: str) -> Path:
        path = (self._root / validate_key(object_key)).resolve()
        if self._root not in path.parents:
            raise ValueError("Invalid storage key")
        return path

    def put(self, object_key: str, data: BinaryIO, content_type: str = "application/octet-stream") -> None:
        path = self._path(object_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as out:
            shutil.copyfileobj(data, out)

    def open(self, object_key: str) -> BinaryIO:
        return self._path(object_key).open("rb")

    def exists(self, object_key: str) -> bool:
        return self._path(object_key).is_file()

    def delete(self, object_key: str) -> None:
        self._path(object_key).unlink(missing_ok=True)

    def scan_status(self, object_key: str) -> str | None:
        # No malware scanner locally; treat files as clean in development only.
        return "NO_THREATS_FOUND" if self.exists(object_key) else None
