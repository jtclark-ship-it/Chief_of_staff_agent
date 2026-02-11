from __future__ import annotations

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.auth.token_store import get_token_store
from app.config import get_settings
from app.utils.errors import NotAuthorized


def get_calendar_service():
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
        creds.refresh(Request())
        store.save({
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
            "expiry": creds.expiry.isoformat() if creds.expiry else None,
        })

    service = build("calendar", "v3", credentials=creds)
    return service
