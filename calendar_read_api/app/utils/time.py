from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


def now_in_tz(tz_name: str) -> datetime:
    return datetime.now(ZoneInfo(tz_name))


def start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def start_of_tomorrow(dt: datetime) -> datetime:
    return start_of_day(dt) + timedelta(days=1)


def start_of_week(dt: datetime) -> datetime:
    """Return Monday 00:00 of the current week."""
    days_since_monday = dt.weekday()
    monday = start_of_day(dt) - timedelta(days=days_since_monday)
    return monday


def to_iso(dt: datetime) -> str:
    return dt.isoformat()


def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s)


def make_time(hour: int, minute: int, tz: ZoneInfo | None = None) -> time:
    return time(hour, minute, tzinfo=tz)
