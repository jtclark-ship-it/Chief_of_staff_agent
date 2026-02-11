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


def _parse_hhmm(s: str) -> tuple[int, int]:
    parts = s.split(":")
    return int(parts[0]), int(parts[1])


def find_gaps(
    events: list[NormalizedEvent],
    min_gap_minutes: int = 0,
    workday_start: str | None = None,
    workday_end: str | None = None,
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
            gap_start = current_end
            gap_end = next_start

            if workday_start and workday_end:
                ws_h, ws_m = _parse_hhmm(workday_start)
                we_h, we_m = _parse_hhmm(workday_end)
                day_start = gap_start.replace(hour=ws_h, minute=ws_m, second=0, microsecond=0)
                day_end = gap_start.replace(hour=we_h, minute=we_m, second=0, microsecond=0)
                gap_start = max(gap_start, day_start)
                gap_end = min(gap_end, day_end)
                if gap_end <= gap_start:
                    continue

            gap_minutes = int((gap_end - gap_start).total_seconds() / 60)
            if gap_minutes >= min_gap_minutes:
                gaps.append(Gap(
                    start=gap_start.isoformat(),
                    end=gap_end.isoformat(),
                    minutes=gap_minutes,
                ))

    return gaps
