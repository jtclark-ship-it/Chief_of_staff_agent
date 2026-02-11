from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class CalendarAPIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict | None = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def to_response(self) -> dict:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class InvalidTimeRange(CalendarAPIError):
    def __init__(self, message: str = "time_max must be after time_min", details: dict | None = None):
        super().__init__("INVALID_TIME_RANGE", message, 400, details)


class RangeExceedsLimit(CalendarAPIError):
    def __init__(self, message: str = "Requested range exceeds allowed limits", details: dict | None = None):
        super().__init__("RANGE_EXCEEDS_LIMIT", message, 400, details)


class MissingTimeWindow(CalendarAPIError):
    def __init__(self):
        super().__init__(
            "MISSING_TIME_WINDOW",
            "Either preset or both time_min and time_max are required",
            400,
        )


class NotAuthorized(CalendarAPIError):
    def __init__(self, message: str = "Not authorized. Visit /auth/start to authorize."):
        super().__init__("NOT_AUTHORIZED", message, 401)


class InsufficientScope(CalendarAPIError):
    def __init__(self, message: str = "Insufficient OAuth scope"):
        super().__init__("INSUFFICIENT_SCOPE", message, 403)


async def calendar_api_error_handler(_request: Request, exc: CalendarAPIError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.to_response())
