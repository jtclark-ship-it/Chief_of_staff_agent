from __future__ import annotations

from app.models.schemas import NormalizedEvent


def redact_event(event: NormalizedEvent) -> NormalizedEvent:
    if event.visibility == "private":
        return event.model_copy(update={
            "summary": "Busy",
            "summary_redacted": True,
            "location": None,
        })
    return event


def redact_events(events: list[NormalizedEvent], redact_private: bool = True) -> list[NormalizedEvent]:
    if not redact_private:
        return events
    return [redact_event(e) for e in events]
