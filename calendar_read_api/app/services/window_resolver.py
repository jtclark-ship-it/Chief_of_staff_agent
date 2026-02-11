from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import get_settings
from app.models.schemas import ResolvedFrom
from app.utils.errors import InvalidTimeRange, MissingTimeWindow, RangeExceedsLimit
from app.utils.time import now_in_tz, start_of_day, start_of_tomorrow, start_of_week, to_iso


PRESETS = {
    "today",
    "tomorrow",
    "next_7_days",
    "next_14_days",
    "this_week",
    "next_week",
    "morning_brief_today",
}


def resolve_preset(preset: str, tz: ZoneInfo) -> tuple[datetime, datetime]:
    now = now_in_tz(str(tz))

    if preset == "today":
        return start_of_day(now), start_of_tomorrow(now)
    elif preset == "tomorrow":
        tom = start_of_day(now) + timedelta(days=1)
        return tom, tom + timedelta(days=1)
    elif preset == "next_7_days":
        return now, now + timedelta(days=7)
    elif preset == "next_14_days":
        return now, now + timedelta(days=14)
    elif preset == "this_week":
        monday = start_of_week(now)
        return monday, monday + timedelta(days=7)
    elif preset == "next_week":
        monday = start_of_week(now)
        next_monday = monday + timedelta(days=7)
        return next_monday, next_monday + timedelta(days=7)
    elif preset == "morning_brief_today":
        return start_of_day(now), start_of_tomorrow(now)
    else:
        raise InvalidTimeRange(f"Unknown preset: {preset}")


class ResolvedWindow:
    def __init__(
        self,
        time_min: str,
        time_max: str,
        resolved_from: ResolvedFrom,
        clamped: bool = False,
        clamp_reason: str | None = None,
    ):
        self.time_min = time_min
        self.time_max = time_max
        self.resolved_from = resolved_from
        self.clamped = clamped
        self.clamp_reason = clamp_reason


def resolve_window(
    time_min: str | None = None,
    time_max: str | None = None,
    preset: str | None = None,
    timezone: str | None = None,
) -> ResolvedWindow:
    settings = get_settings()
    tz_name = timezone or settings.DEFAULT_TIMEZONE
    tz = ZoneInfo(tz_name)

    if preset:
        dt_min, dt_max = resolve_preset(preset, tz)
        resolved_from = ResolvedFrom(preset=preset, timezone=tz_name)
    elif time_min and time_max:
        dt_min = datetime.fromisoformat(time_min)
        dt_max = datetime.fromisoformat(time_max)
        if dt_min.tzinfo is None:
            dt_min = dt_min.replace(tzinfo=tz)
        if dt_max.tzinfo is None:
            dt_max = dt_max.replace(tzinfo=tz)
        resolved_from = ResolvedFrom(explicit=True, timezone=tz_name)
    else:
        raise MissingTimeWindow()

    if dt_max <= dt_min:
        raise InvalidTimeRange()

    now = now_in_tz(tz_name)
    max_future = now + timedelta(days=settings.MAX_LOOKAHEAD_DAYS)
    max_past = now - timedelta(days=settings.MAX_LOOKBACK_DAYS)

    clamped = False
    clamp_reason = None

    if dt_min < max_past or dt_max > max_future:
        if not settings.ALLOW_CLAMPING:
            raise RangeExceedsLimit(
                f"Range exceeds limits: max lookback={settings.MAX_LOOKBACK_DAYS}d, "
                f"max lookahead={settings.MAX_LOOKAHEAD_DAYS}d",
                details={
                    "max_lookback_days": settings.MAX_LOOKBACK_DAYS,
                    "max_lookahead_days": settings.MAX_LOOKAHEAD_DAYS,
                },
            )
        reasons = []
        if dt_min < max_past:
            dt_min = max_past
            reasons.append(f"time_min clamped to {settings.MAX_LOOKBACK_DAYS}d lookback")
        if dt_max > max_future:
            dt_max = max_future
            reasons.append(f"time_max clamped to {settings.MAX_LOOKAHEAD_DAYS}d lookahead")
        clamped = True
        clamp_reason = "; ".join(reasons)

    return ResolvedWindow(
        time_min=to_iso(dt_min),
        time_max=to_iso(dt_max),
        resolved_from=resolved_from,
        clamped=clamped,
        clamp_reason=clamp_reason,
    )
