from fastapi import FastAPI

from app.api.routes_auth import router as auth_router
from app.api.routes_calendar import router as calendar_router
from app.utils.errors import CalendarAPIError, calendar_api_error_handler
from app.utils.logging import setup_logging

setup_logging()

app = FastAPI(
    title="Calendar Read API",
    version="1.0.0",
    description="Read-only access to Google Calendar with normalized JSON responses.",
)

app.add_exception_handler(CalendarAPIError, calendar_api_error_handler)

app.include_router(auth_router)
app.include_router(calendar_router)


@app.get("/health")
def health():
    return {"status": "ok"}
