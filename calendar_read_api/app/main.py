import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google.auth.exceptions import GoogleAuthError
from googleapiclient.errors import HttpError

from app.api.routes_auth import router as auth_router
from app.api.routes_calendar import router as calendar_router
from app.utils.errors import CalendarAPIError, calendar_api_error_handler
from app.utils.logging import get_logger, setup_logging

setup_logging()

app = FastAPI(
    title="Calendar Read API",
    version="1.0.0",
    description="Read-only access to Google Calendar with normalized JSON responses.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(CalendarAPIError, calendar_api_error_handler)


@app.exception_handler(HttpError)
async def google_http_error_handler(_request: Request, exc: HttpError) -> JSONResponse:
    logger = get_logger()
    logger.error("Google API HttpError: %s", exc)
    return JSONResponse(
        status_code=exc.resp.status if exc.resp else 502,
        content={"error": {"code": "GOOGLE_API_ERROR", "message": str(exc), "details": {}}},
    )


@app.exception_handler(GoogleAuthError)
async def google_auth_error_handler(_request: Request, exc: GoogleAuthError) -> JSONResponse:
    logger = get_logger()
    logger.error("Google auth error: %s", exc)
    return JSONResponse(
        status_code=401,
        content={"error": {"code": "GOOGLE_AUTH_ERROR", "message": str(exc), "details": {}}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger = get_logger()
    logger.error("Unhandled exception:\n%s", traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": str(exc), "details": {}}},
    )

app.include_router(auth_router)
app.include_router(calendar_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/debug/calendars")
def debug_calendars():
    """Temporary debug endpoint — returns 200 with diagnostic info."""
    import os
    from app.config import get_settings
    from app.auth.token_store import get_token_store

    settings = get_settings()
    result = {
        "cwd": os.getcwd(),
        "token_store_path": settings.TOKEN_STORE_PATH,
        "resolved_path": os.path.abspath(settings.TOKEN_STORE_PATH),
        "token_file_exists": os.path.exists(settings.TOKEN_STORE_PATH),
    }

    store = get_token_store(settings.TOKEN_STORE_TYPE, settings.TOKEN_STORE_PATH)
    token_data = store.load()
    result["token_loaded"] = token_data is not None

    if not token_data:
        result["error"] = "No token found"
        return result

    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        creds = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri"),
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=token_data.get("scopes"),
        )
        result["creds_valid"] = creds.valid
        result["creds_expired"] = creds.expired

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            result["refreshed"] = True

        service = build("calendar", "v3", credentials=creds)
        raw = service.calendarList().list().execute()
        result["calendars"] = raw.get("items", [])
        result["success"] = True
    except Exception as exc:
        result["error"] = str(exc)
        result["traceback"] = traceback.format_exc()

    return result
