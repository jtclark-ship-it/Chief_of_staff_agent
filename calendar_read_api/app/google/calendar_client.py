from __future__ import annotations

from typing import Any

from app.utils.logging import get_logger


def list_calendars(service: Any) -> list[dict]:
    logger = get_logger()
    logger.debug("Calling calendarList().list()")
    result = service.calendarList().list().execute()
    items = result.get("items", [])
    logger.debug("calendarList returned %d items", len(items))
    return items


def list_events(
    service: Any,
    calendar_id: str,
    time_min: str,
    time_max: str,
    max_results: int = 250,
    include_cancelled: bool = False,
) -> list[dict]:
    events: list[dict] = []
    page_token = None

    while True:
        request = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            maxResults=min(max_results - len(events), 2500),
            showDeleted=include_cancelled,
            pageToken=page_token,
        )
        result = request.execute()
        items = result.get("items", [])
        events.extend(items)

        if len(events) >= max_results:
            events = events[:max_results]
            break

        page_token = result.get("nextPageToken")
        if not page_token:
            break

    return events


def query_freebusy(
    service: Any,
    time_min: str,
    time_max: str,
    calendar_ids: list[str],
) -> dict[str, list[dict]]:
    body = {
        "timeMin": time_min,
        "timeMax": time_max,
        "items": [{"id": cid} for cid in calendar_ids],
    }
    result = service.freebusy().query(body=body).execute()
    calendars = result.get("calendars", {})

    busy: dict[str, list[dict]] = {}
    for cal_id, cal_data in calendars.items():
        busy[cal_id] = cal_data.get("busy", [])

    return busy
