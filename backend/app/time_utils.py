"""Time helpers. All storage is UTC; all API output is Asia/Manila."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

MANILA_TZ = ZoneInfo("Asia/Manila")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def to_manila(value: datetime) -> datetime:
    return as_utc(value).astimezone(MANILA_TZ)


def iso_manila(value: datetime) -> str:
    """RFC3339 timestamp with the Asia/Manila (+08:00) offset."""

    return to_manila(value).isoformat()
