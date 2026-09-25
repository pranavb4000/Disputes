"""Choose the storage backend from settings."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.storage.base import FileStorage
from app.storage.local import LocalFileStorage


@lru_cache
def get_storage() -> FileStorage:
    settings = get_settings()
    if settings.storage_backend == "s3":
        from app.storage.s3 import S3FileStorage

        return S3FileStorage(settings.s3_bucket, settings.aws_region, settings.s3_kms_key_id)
    if not settings.is_development:
        raise RuntimeError("Local file storage is only allowed in development/test")
    return LocalFileStorage(settings.storage_local_path)
