from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_calendar_service
from app.config import get_settings
from app.google.calendar_client import list_calendars, list_events, query_freebusy
from app.models.schemas import (
    CalendarEntry,
    CalendarsResponse,
    CompactEvent,
    EventsResponse,
    FreeBusyRequest,
    FreeBusyResponse,
    BusyBlock,
    SnapshotResponse,
)
from app.services.normalization import normalize_events
from app.services.redaction import redact_events
from app.services.snapshot import compute_summary, find_conflicts, find_gaps, to_compact
from app.services.window_resolver import resolve_window
from app.utils.logging import get_logger

router = APIRouter(prefix="/v1", tags=["calendar"])


@router.get("/calendars", response_model=CalendarsResponse)
def get_calendars(service=Depends(get_calendar_service)):
    try:
        raw = list_calendars(service)
        calendars = [
            CalendarEntry(
                calendar_id=c.get("id", ""),
                summary=c.get("summary"),
                timeZone=c.get("timeZone"),
                accessRole=c.get("accessRole"),
            )
            for c in raw
        ]
        return CalendarsResponse(calendars=calendars)
    except Exception:
        return CalendarsResponse(
            calendars=[CalendarEntry(calendar_id="primary", summary="Primary")]
        )


@router.get("/events", response_model=EventsResponse)
def get_events(
    calendar_id: str = Query(default="primary"),
    time_min: str | None = Query(default=None),
    time_max: str | None = Query(default=None),
    preset: str | None = Query(default=None),
    timezone: str | None = Query(default=None),
    include_cancelled: bool = Query(default=False),
    max_results: int = Query(default=250),
    redact_private: bool = Query(default=True),
    service=Depends(get_calendar_service),
):
    logger = get_logger()
    settings = get_settings()

    max_results = min(max_results, settings.MAX_EVENTS_HARD_CAP)

    window = resolve_window(time_min, time_max, preset, timezone)

    raw_events = list_events(
        service,
        calendar_id=calendar_id,
        time_min=window.time_min,
        time_max=window.time_max,
        max_results=max_results,
        include_cancelled=include_cancelled,
    )

    events = normalize_events(raw_events)
    events = redact_events(events, redact_private=redact_private)

    tz = timezone or settings.DEFAULT_TIMEZONE
    logger.info(
        "GET /v1/events | calendar=%s | window=%s..%s | resolved_from=%s | event_count=%d | clamped=%s",
        calendar_id, window.time_min, window.time_max,
        window.resolved_from.preset or "explicit", len(events), window.clamped,
    )

    return EventsResponse(
        calendar_id=calendar_id,
        timezone=tz,
        time_min=window.time_min,
        time_max=window.time_max,
        resolved_from=window.resolved_from,
        clamped=window.clamped,
        clamp_reason=window.clamp_reason,
        events=events,
    )


@router.post("/freebusy", response_model=FreeBusyResponse)
def post_freebusy(
    body: FreeBusyRequest,
    service=Depends(get_calendar_service),
):
    logger = get_logger()
    settings = get_settings()

    window = resolve_window(body.time_min, body.time_max, body.preset, body.timezone)

    raw_busy = query_freebusy(
        service,
        time_min=window.time_min,
        time_max=window.time_max,
        calendar_ids=body.calendar_ids,
    )

    busy = {
        cal_id: [BusyBlock(start=b["start"], end=b["end"]) for b in blocks]
        for cal_id, blocks in raw_busy.items()
    }

    tz = body.timezone or settings.DEFAULT_TIMEZONE
    logger.info(
        "POST /v1/freebusy | window=%s..%s | calendars=%d | clamped=%s",
        window.time_min, window.time_max, len(body.calendar_ids), window.clamped,
    )

    return FreeBusyResponse(
        time_min=window.time_min,
        time_max=window.time_max,
        timezone=tz,
        resolved_from=window.resolved_from,
        clamped=window.clamped,
        clamp_reason=window.clamp_reason,
        busy=busy,
    )


@router.get("/snapshot", response_model=SnapshotResponse)
def get_snapshot(
    calendar_id: str = Query(default="primary"),
    time_min: str | None = Query(default=None),
    time_max: str | None = Query(default=None),
    preset: str | None = Query(default=None),
    timezone: str | None = Query(default=None),
    include_cancelled: bool = Query(default=False),
    max_results: int = Query(default=250),
    redact_private: bool = Query(default=True),
    workday_start: str = Query(default="08:00"),
    workday_end: str = Query(default="18:00"),
    min_gap_minutes: int = Query(default=0),
    service=Depends(get_calendar_service),
):
    logger = get_logger()
    settings = get_settings()

    max_results = min(max_results, settings.MAX_EVENTS_HARD_CAP)

    window = resolve_window(time_min, time_max, preset, timezone)

    raw_events = list_events(
        service,
        calendar_id=calendar_id,
        time_min=window.time_min,
        time_max=window.time_max,
        max_results=max_results,
        include_cancelled=include_cancelled,
    )

    events = normalize_events(raw_events)
    events = redact_events(events, redact_private=redact_private)

    summary = compute_summary(events)
    compact = to_compact(events)
    conflicts = find_conflicts(events)
    gaps = find_gaps(events, min_gap_minutes=min_gap_minutes, workday_start=workday_start, workday_end=workday_end)

    tz = timezone or settings.DEFAULT_TIMEZONE
    logger.info(
        "GET /v1/snapshot | calendar=%s | window=%s..%s | event_count=%d | conflicts=%d | gaps=%d | clamped=%s",
        calendar_id, window.time_min, window.time_max,
        len(events), len(conflicts), len(gaps), window.clamped,
    )

    return SnapshotResponse(
        calendar_id=calendar_id,
        timezone=tz,
        time_min=window.time_min,
        time_max=window.time_max,
        resolved_from=window.resolved_from,
        clamped=window.clamped,
        clamp_reason=window.clamp_reason,
        summary=summary,
        events_compact=compact,
        conflicts=conflicts,
        gaps=gaps,
    )
