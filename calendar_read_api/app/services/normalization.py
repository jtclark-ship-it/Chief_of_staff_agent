from __future__ import annotations

from app.models.schemas import NormalizedEvent


def normalize_event(raw: dict) -> NormalizedEvent:
    start_raw = raw.get("start", {})
    end_raw = raw.get("end", {})

    is_all_day = "date" in start_raw and "dateTime" not in start_raw

    start = start_raw.get("dateTime") or start_raw.get("date", "")
    end = end_raw.get("dateTime") or end_raw.get("date", "")

    attendees = raw.get("attendees", [])

    return NormalizedEvent(
        event_id=raw.get("id", ""),
        status=raw.get("status", "confirmed"),
        summary=raw.get("summary", "(No title)"),
        summary_redacted=False,
        description_present=bool(raw.get("description")),
        location=raw.get("location"),
        start=start,
        end=end,
        is_all_day=is_all_day,
        attendees_count=len(attendees),
        organizer_email=raw.get("organizer", {}).get("email"),
        visibility=raw.get("visibility", "default"),
        transparency=raw.get("transparency", "opaque"),
        html_link=raw.get("htmlLink"),
    )


def normalize_events(raw_events: list[dict]) -> list[NormalizedEvent]:
    return [normalize_event(e) for e in raw_events]
