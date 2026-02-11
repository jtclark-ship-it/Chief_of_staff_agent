from __future__ import annotations

from app.services.normalization import normalize_event, normalize_events


class TestNormalizeEvent:
    def test_timed_event(self):
        raw = {
            "id": "abc123",
            "status": "confirmed",
            "summary": "Team Standup",
            "description": "Daily sync",
            "location": "Room A",
            "start": {"dateTime": "2025-06-11T09:00:00-06:00"},
            "end": {"dateTime": "2025-06-11T09:30:00-06:00"},
            "attendees": [{"email": "a@b.com"}, {"email": "c@d.com"}],
            "organizer": {"email": "a@b.com"},
            "visibility": "default",
            "transparency": "opaque",
            "htmlLink": "https://calendar.google.com/event?eid=abc",
        }

        event = normalize_event(raw)

        assert event.event_id == "abc123"
        assert event.status == "confirmed"
        assert event.summary == "Team Standup"
        assert event.summary_redacted is False
        assert event.description_present is True
        assert event.location == "Room A"
        assert event.start == "2025-06-11T09:00:00-06:00"
        assert event.end == "2025-06-11T09:30:00-06:00"
        assert event.is_all_day is False
        assert event.attendees_count == 2
        assert event.organizer_email == "a@b.com"
        assert event.visibility == "default"
        assert event.transparency == "opaque"
        assert event.html_link == "https://calendar.google.com/event?eid=abc"

    def test_all_day_event(self):
        raw = {
            "id": "allday1",
            "status": "confirmed",
            "summary": "Company Holiday",
            "start": {"date": "2025-06-11"},
            "end": {"date": "2025-06-12"},
        }

        event = normalize_event(raw)

        assert event.is_all_day is True
        assert event.start == "2025-06-11"
        assert event.end == "2025-06-12"

    def test_no_description(self):
        raw = {
            "id": "nodesc",
            "status": "confirmed",
            "summary": "Quick chat",
            "start": {"dateTime": "2025-06-11T10:00:00-06:00"},
            "end": {"dateTime": "2025-06-11T10:15:00-06:00"},
        }

        event = normalize_event(raw)
        assert event.description_present is False

    def test_no_summary(self):
        raw = {
            "id": "nosum",
            "status": "confirmed",
            "start": {"dateTime": "2025-06-11T10:00:00-06:00"},
            "end": {"dateTime": "2025-06-11T10:15:00-06:00"},
        }

        event = normalize_event(raw)
        assert event.summary == "(No title)"

    def test_normalize_events_list(self):
        raw_list = [
            {
                "id": "e1",
                "status": "confirmed",
                "summary": "A",
                "start": {"dateTime": "2025-06-11T09:00:00-06:00"},
                "end": {"dateTime": "2025-06-11T09:30:00-06:00"},
            },
            {
                "id": "e2",
                "status": "confirmed",
                "summary": "B",
                "start": {"date": "2025-06-11"},
                "end": {"date": "2025-06-12"},
            },
        ]
        events = normalize_events(raw_list)
        assert len(events) == 2
        assert events[0].event_id == "e1"
        assert events[1].is_all_day is True
