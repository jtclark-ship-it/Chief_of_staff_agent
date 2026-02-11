from __future__ import annotations

from datetime import datetime

from app.models.schemas import (
    CompactEvent,
    Conflict,
    Gap,
    NormalizedEvent,
    SnapshotSummary,
)


def compute_summary(events: list[NormalizedEvent]) -> SnapshotSummary:
    event_count = len(events)
    all_day_count = sum(1 for e in events if e.is_all_day)
    meeting_minutes = 0
    for e in events:
        if e.is_all_day:
            continue
        try:
            start = datetime.fromisoformat(e.start)
            end = datetime.fromisoformat(e.end)
            meeting_minutes += int((end - start).total_seconds() / 60)
        except (ValueError, TypeError):
            pass
    return SnapshotSummary(
        event_count=event_count,
        meeting_minutes=meeting_minutes,
        all_day_count=all_day_count,
    )


def to_compact(events: list[NormalizedEvent]) -> list[CompactEvent]:
    return [
        CompactEvent(
            event_id=e.event_id,
            start=e.start,
            end=e.end,
            summary=e.summary,
            summary_redacted=e.summary_redacted,
            location=e.location,
        )
        for e in events
    ]


def find_conflicts(events: list[NormalizedEvent]) -> list[Conflict]:
    timed = [
        e for e in events
        if not e.is_all_day
        and e.status != "cancelled"
        and e.transparency != "transparent"
    ]

    conflicts: list[Conflict] = []
    for i in range(len(timed)):
        for j in range(i + 1, len(timed)):
            a = timed[i]
            b = timed[j]
            try:
                start_a = datetime.fromisoformat(a.start)
                end_a = datetime.fromisoformat(a.end)
                start_b = datetime.fromisoformat(b.start)
                end_b = datetime.fromisoformat(b.end)
            except (ValueError, TypeError):
                continue

            overlap_start = max(start_a, start_b)
            overlap_end = min(end_a, end_b)
            if overlap_start < overlap_end:
                conflicts.append(Conflict(
                    type="overlap",
                    start=overlap_start.isoformat(),
                    end=overlap_end.isoformat(),
                    events=[a.event_id, b.event_id],
                ))

    return conflicts


def find_gaps(
    events: list[NormalizedEvent],
    min_gap_minutes: int = 0,
) -> list[Gap]:
    timed = [
        e for e in events
        if not e.is_all_day
        and e.status != "cancelled"
        and e.transparency != "transparent"
    ]

    parsed: list[tuple[datetime, datetime]] = []
    for e in timed:
        try:
            s = datetime.fromisoformat(e.start)
            en = datetime.fromisoformat(e.end)
            parsed.append((s, en))
        except (ValueError, TypeError):
            pass

    parsed.sort(key=lambda x: x[0])

    gaps: list[Gap] = []
    for i in range(len(parsed) - 1):
        current_end = parsed[i][1]
        next_start = parsed[i + 1][0]
        if next_start > current_end:
            gap_minutes = int((next_start - current_end).total_seconds() / 60)
            if gap_minutes >= min_gap_minutes:
                gaps.append(Gap(
                    start=current_end.isoformat(),
                    end=next_start.isoformat(),
                    minutes=gap_minutes,
                ))

    return gaps
