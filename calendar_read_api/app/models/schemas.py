from __future__ import annotations

from pydantic import BaseModel, Field


class ResolvedFrom(BaseModel):
    preset: str | None = None
    timezone: str | None = None
    explicit: bool = False


class NormalizedEvent(BaseModel):
    event_id: str
    status: str
    summary: str
    summary_redacted: bool = False
    description_present: bool = False
    location: str | None = None
    start: str
    end: str
    is_all_day: bool = False
    attendees_count: int = 0
    organizer_email: str | None = None
    visibility: str = "default"
    transparency: str = "opaque"
    html_link: str | None = None


class CalendarEntry(BaseModel):
    calendar_id: str
    summary: str | None = None
    timeZone: str | None = None
    accessRole: str | None = None


class CalendarsResponse(BaseModel):
    calendars: list[CalendarEntry]


class EventsResponse(BaseModel):
    calendar_id: str
    timezone: str
    time_min: str
    time_max: str
    resolved_from: ResolvedFrom
    clamped: bool = False
    clamp_reason: str | None = None
    events: list[NormalizedEvent]


class BusyBlock(BaseModel):
    start: str
    end: str


class FreeBusyRequest(BaseModel):
    time_min: str | None = None
    time_max: str | None = None
    preset: str | None = None
    calendar_ids: list[str] = Field(default_factory=lambda: ["primary"])
    timezone: str | None = None


class FreeBusyResponse(BaseModel):
    time_min: str
    time_max: str
    timezone: str
    resolved_from: ResolvedFrom
    clamped: bool = False
    clamp_reason: str | None = None
    busy: dict[str, list[BusyBlock]]


class SnapshotSummary(BaseModel):
    event_count: int
    meeting_minutes: int
    all_day_count: int


class CompactEvent(BaseModel):
    event_id: str
    start: str
    end: str
    summary: str
    summary_redacted: bool = False
    location: str | None = None


class Conflict(BaseModel):
    type: str = "overlap"
    start: str
    end: str
    events: list[str]


class Gap(BaseModel):
    start: str
    end: str
    minutes: int


class SnapshotResponse(BaseModel):
    calendar_id: str
    timezone: str
    time_min: str
    time_max: str
    resolved_from: ResolvedFrom
    clamped: bool = False
    clamp_reason: str | None = None
    summary: SnapshotSummary
    events_compact: list[CompactEvent]
    conflicts: list[Conflict]
    gaps: list[Gap]


class AuthStatusResponse(BaseModel):
    authorized: bool
    scopes: list[str] = Field(default_factory=list)
    token_expiry: str | None = None


class RevokeResponse(BaseModel):
    revoked: bool


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail
