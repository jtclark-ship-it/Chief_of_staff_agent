from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app.main import app

TZ = ZoneInfo("America/Denver")
FIXED_NOW = datetime(2025, 6, 11, 10, 30, 0, tzinfo=TZ)

MOCK_EVENTS = [
    {
        "id": "ev1",
        "status": "confirmed",
        "summary": "Test Meeting",
        "start": {"dateTime": "2025-06-11T09:00:00-06:00"},
        "end": {"dateTime": "2025-06-11T10:00:00-06:00"},
        "visibility": "default",
        "transparency": "opaque",
    },
    {
        "id": "ev2",
        "status": "confirmed",
        "summary": "Private",
        "start": {"dateTime": "2025-06-11T11:00:00-06:00"},
        "end": {"dateTime": "2025-06-11T12:00:00-06:00"},
        "visibility": "private",
        "transparency": "opaque",
    },
]


def _mock_calendar_service():
    service = MagicMock()
    # events().list().execute()
    events_list = MagicMock()
    events_list.execute.return_value = {"items": MOCK_EVENTS}
    service.events.return_value.list.return_value = events_list

    # calendarList().list().execute()
    cal_list = MagicMock()
    cal_list.execute.return_value = {
        "items": [
            {"id": "primary", "summary": "My Calendar", "timeZone": "America/Denver", "accessRole": "owner"}
        ]
    }
    service.calendarList.return_value.list.return_value = cal_list

    # freebusy().query().execute()
    freebusy_query = MagicMock()
    freebusy_query.execute.return_value = {
        "calendars": {
            "primary": {
                "busy": [
                    {"start": "2025-06-11T09:00:00-06:00", "end": "2025-06-11T10:00:00-06:00"}
                ]
            }
        }
    }
    service.freebusy.return_value.query.return_value = freebusy_query

    return service


@pytest.fixture
def client():
    mock_service = _mock_calendar_service()
    app.dependency_overrides = {}
    from app.auth.dependencies import get_calendar_service
    app.dependency_overrides[get_calendar_service] = lambda: mock_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides = {}


def _patch_now():
    return patch("app.services.window_resolver.now_in_tz", return_value=FIXED_NOW)


class TestEventsRoute:
    def test_events_with_preset(self, client):
        with _patch_now():
            resp = client.get("/v1/events?preset=today")
        assert resp.status_code == 200
        data = resp.json()
        assert data["calendar_id"] == "primary"
        assert len(data["events"]) == 2
        assert data["resolved_from"]["preset"] == "today"
        assert data["clamped"] is False

    def test_events_with_explicit_window(self, client):
        with _patch_now():
            resp = client.get(
                "/v1/events?time_min=2025-06-11T00:00:00-06:00&time_max=2025-06-12T00:00:00-06:00"
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolved_from"]["explicit"] is True

    def test_events_missing_window_returns_400(self, client):
        resp = client.get("/v1/events")
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"]["code"] == "MISSING_TIME_WINDOW"

    def test_events_redaction_default(self, client):
        with _patch_now():
            resp = client.get("/v1/events?preset=today")
        data = resp.json()
        # Second event is private → should be redacted
        private_event = [e for e in data["events"] if e["event_id"] == "ev2"][0]
        assert private_event["summary"] == "Busy"
        assert private_event["summary_redacted"] is True

    def test_events_redaction_disabled(self, client):
        with _patch_now():
            resp = client.get("/v1/events?preset=today&redact_private=false")
        data = resp.json()
        private_event = [e for e in data["events"] if e["event_id"] == "ev2"][0]
        assert private_event["summary"] == "Private"
        assert private_event["summary_redacted"] is False


class TestCalendarsRoute:
    def test_list_calendars(self, client):
        resp = client.get("/v1/calendars")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["calendars"]) == 1
        assert data["calendars"][0]["calendar_id"] == "primary"


class TestFreeBusyRoute:
    def test_freebusy_with_preset(self, client):
        with _patch_now():
            resp = client.post(
                "/v1/freebusy",
                json={"preset": "today", "calendar_ids": ["primary"]},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "primary" in data["busy"]
        assert len(data["busy"]["primary"]) == 1

    def test_freebusy_missing_window(self, client):
        resp = client.post(
            "/v1/freebusy",
            json={"calendar_ids": ["primary"]},
        )
        assert resp.status_code == 400


class TestSnapshotRoute:
    def test_snapshot_with_preset(self, client):
        with _patch_now():
            resp = client.get("/v1/snapshot?preset=morning_brief_today")
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["event_count"] == 2
        assert len(data["events_compact"]) == 2
        assert isinstance(data["conflicts"], list)
        assert isinstance(data["gaps"], list)

    def test_snapshot_missing_window(self, client):
        resp = client.get("/v1/snapshot")
        assert resp.status_code == 400


class TestHealthRoute:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
