from __future__ import annotations

from app.models.schemas import NormalizedEvent
from app.services.snapshot import compute_summary, find_conflicts, find_gaps, to_compact


def _event(
    event_id: str,
    start: str,
    end: str,
    is_all_day: bool = False,
    status: str = "confirmed",
    transparency: str = "opaque",
    summary: str = "Event",
) -> NormalizedEvent:
    return NormalizedEvent(
        event_id=event_id,
        status=status,
        summary=summary,
        summary_redacted=False,
        description_present=False,
        location=None,
        start=start,
        end=end,
        is_all_day=is_all_day,
        attendees_count=0,
        organizer_email=None,
        visibility="default",
        transparency=transparency,
        html_link=None,
    )


class TestComputeSummary:
    def test_basic_summary(self):
        events = [
            _event("e1", "2025-06-11T09:00:00-06:00", "2025-06-11T10:00:00-06:00"),
            _event("e2", "2025-06-11T10:00:00-06:00", "2025-06-11T11:00:00-06:00"),
            _event("e3", "2025-06-11", "2025-06-12", is_all_day=True),
        ]
        summary = compute_summary(events)
        assert summary.event_count == 3
        assert summary.all_day_count == 1
        assert summary.meeting_minutes == 120  # 2 x 60 min

    def test_empty(self):
        summary = compute_summary([])
        assert summary.event_count == 0
        assert summary.meeting_minutes == 0
        assert summary.all_day_count == 0


class TestFindConflicts:
    def test_overlapping_events(self):
        events = [
            _event("e1", "2025-06-11T09:00:00-06:00", "2025-06-11T10:00:00-06:00"),
            _event("e2", "2025-06-11T09:30:00-06:00", "2025-06-11T10:30:00-06:00"),
        ]
        conflicts = find_conflicts(events)
        assert len(conflicts) == 1
        assert set(conflicts[0].events) == {"e1", "e2"}
        assert conflicts[0].start == "2025-06-11T09:30:00-06:00"
        assert conflicts[0].end == "2025-06-11T10:00:00-06:00"

    def test_no_overlap(self):
        events = [
            _event("e1", "2025-06-11T09:00:00-06:00", "2025-06-11T10:00:00-06:00"),
            _event("e2", "2025-06-11T10:00:00-06:00", "2025-06-11T11:00:00-06:00"),
        ]
        conflicts = find_conflicts(events)
        assert len(conflicts) == 0

    def test_cancelled_events_ignored(self):
        events = [
            _event("e1", "2025-06-11T09:00:00-06:00", "2025-06-11T10:00:00-06:00"),
            _event("e2", "2025-06-11T09:30:00-06:00", "2025-06-11T10:30:00-06:00", status="cancelled"),
        ]
        conflicts = find_conflicts(events)
        assert len(conflicts) == 0

    def test_transparent_events_ignored(self):
        events = [
            _event("e1", "2025-06-11T09:00:00-06:00", "2025-06-11T10:00:00-06:00"),
            _event("e2", "2025-06-11T09:30:00-06:00", "2025-06-11T10:30:00-06:00", transparency="transparent"),
        ]
        conflicts = find_conflicts(events)
        assert len(conflicts) == 0

    def test_all_day_events_ignored(self):
        events = [
            _event("e1", "2025-06-11", "2025-06-12", is_all_day=True),
            _event("e2", "2025-06-11T09:00:00-06:00", "2025-06-11T10:00:00-06:00"),
        ]
        conflicts = find_conflicts(events)
        assert len(conflicts) == 0


class TestFindGaps:
    def test_gap_between_events(self):
        events = [
            _event("e1", "2025-06-11T09:00:00-06:00", "2025-06-11T10:00:00-06:00"),
            _event("e2", "2025-06-11T11:30:00-06:00", "2025-06-11T12:00:00-06:00"),
        ]
        gaps = find_gaps(events, min_gap_minutes=0)
        assert len(gaps) == 1
        assert gaps[0].minutes == 90

    def test_no_gap(self):
        events = [
            _event("e1", "2025-06-11T09:00:00-06:00", "2025-06-11T10:00:00-06:00"),
            _event("e2", "2025-06-11T10:00:00-06:00", "2025-06-11T11:00:00-06:00"),
        ]
        gaps = find_gaps(events, min_gap_minutes=0)
        assert len(gaps) == 0

    def test_min_gap_filter(self):
        events = [
            _event("e1", "2025-06-11T09:00:00-06:00", "2025-06-11T10:00:00-06:00"),
            _event("e2", "2025-06-11T10:15:00-06:00", "2025-06-11T11:00:00-06:00"),
        ]
        gaps = find_gaps(events, min_gap_minutes=30)
        assert len(gaps) == 0

        gaps = find_gaps(events, min_gap_minutes=15)
        assert len(gaps) == 1

    def test_all_day_ignored_for_gaps(self):
        events = [
            _event("e1", "2025-06-11", "2025-06-12", is_all_day=True),
        ]
        gaps = find_gaps(events, min_gap_minutes=0)
        assert len(gaps) == 0


class TestToCompact:
    def test_compact_conversion(self):
        events = [
            _event("e1", "2025-06-11T09:00:00-06:00", "2025-06-11T10:00:00-06:00", summary="Standup"),
        ]
        compact = to_compact(events)
        assert len(compact) == 1
        assert compact[0].event_id == "e1"
        assert compact[0].summary == "Standup"
