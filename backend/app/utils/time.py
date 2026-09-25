"""Time helpers. The database stores naive UTC timestamps; the UI displays IST."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

# India has no daylight saving, so a fixed offset is exact. (zoneinfo would need the extra
# `tzdata` package on Windows.)
IST = timezone(timedelta(hours=5, minutes=30), name="IST")


def utcnow() -> datetime:
    """Current UTC time without tzinfo, matching Oracle TIMESTAMP columns."""
    return datetime.now(UTC).replace(tzinfo=None)


def as_utc(value: datetime | None) -> datetime | None:
    """Attach UTC to a naive DB timestamp so JSON output carries an explicit offset."""
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)
