from __future__ import annotations

from app.models.schemas import NormalizedEvent
from app.services.redaction import redact_events


def _make_event(visibility: str = "default", summary: str = "Meeting", location: str | None = "Room A") -> NormalizedEvent:
    return NormalizedEvent(
        event_id="test1",
        status="confirmed",
        summary=summary,
        summary_redacted=False,
        description_present=False,
        location=location,
        start="2025-06-11T09:00:00-06:00",
        end="2025-06-11T09:30:00-06:00",
        is_all_day=False,
        attendees_count=2,
        organizer_email="a@b.com",
        visibility=visibility,
        transparency="opaque",
        html_link=None,
    )


class TestRedaction:
    def test_private_event_redacted(self):
        events = [_make_event(visibility="private", summary="Secret Meeting", location="CEO Office")]
        result = redact_events(events, redact_private=True)
        assert result[0].summary == "Busy"
        assert result[0].summary_redacted is True
        assert result[0].location is None

    def test_public_event_not_redacted(self):
        events = [_make_event(visibility="public", summary="All Hands")]
        result = redact_events(events, redact_private=True)
        assert result[0].summary == "All Hands"
        assert result[0].summary_redacted is False
        assert result[0].location == "Room A"

    def test_default_visibility_not_redacted(self):
        events = [_make_event(visibility="default")]
        result = redact_events(events, redact_private=True)
        assert result[0].summary == "Meeting"
        assert result[0].summary_redacted is False

    def test_redaction_disabled(self):
        events = [_make_event(visibility="private", summary="Secret")]
        result = redact_events(events, redact_private=False)
        assert result[0].summary == "Secret"
        assert result[0].summary_redacted is False

    def test_timestamps_preserved_after_redaction(self):
        events = [_make_event(visibility="private")]
        result = redact_events(events, redact_private=True)
        assert result[0].start == "2025-06-11T09:00:00-06:00"
        assert result[0].end == "2025-06-11T09:30:00-06:00"

    def test_redaction_does_not_mutate_original(self):
        events = [_make_event(visibility="private", summary="Secret", location="Room A")]
        redact_events(events, redact_private=True)
        assert events[0].summary == "Secret"
        assert events[0].location == "Room A"
