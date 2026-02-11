from __future__ import annotations

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.auth.token_store import get_token_store
from app.config import get_settings
from app.utils.errors import NotAuthorized
from app.utils.logging import get_logger


def get_calendar_service():
    logger = get_logger()
    settings = get_settings()
    store = get_token_store(settings.TOKEN_STORE_TYPE, settings.TOKEN_STORE_PATH)
    token_data = store.load()

    if not token_data:
        raise NotAuthorized()

    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes"),
    )

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError as exc:
            logger.error("Token refresh failed: %s", exc)
            store.clear()
            raise NotAuthorized("Token expired and refresh failed. Visit /auth/start to re-authorize.")
        store.save({
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes) if creds.scopes else [],
            "expiry": creds.expiry.isoformat() if creds.expiry else None,
        })

    service = build("calendar", "v3", credentials=creds)
    return service
