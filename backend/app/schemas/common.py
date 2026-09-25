"""Shared schema types."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from pydantic import PlainSerializer


def _to_utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


# Datetimes always leave the API as explicit UTC, e.g. "2026-09-24T10:15:00Z".
UtcDatetime = Annotated[datetime, PlainSerializer(_to_utc_iso, return_type=str, when_used="json")]
