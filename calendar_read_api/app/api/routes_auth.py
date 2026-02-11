from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.auth.oauth import build_flow
from app.auth.token_store import get_token_store
from app.config import get_settings
from app.models.schemas import AuthStatusResponse, RevokeResponse
from app.utils.logging import get_logger

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/start")
def auth_start():
    flow = build_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return RedirectResponse(url=auth_url)


@router.get("/callback")
def auth_callback(request: Request):
    logger = get_logger()
    settings = get_settings()

    code = request.query_params.get("code")
    if not code:
        return {"error": "Missing authorization code"}

    flow = build_flow()
    flow.fetch_token(code=code)
    creds = flow.credentials

    store = get_token_store(settings.TOKEN_STORE_TYPE, settings.TOKEN_STORE_PATH)
    store.save({
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else [],
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
    })

    logger.info("OAuth callback: tokens persisted successfully")
    return {"message": "Authorization successful. You can close this window."}


@router.get("/status", response_model=AuthStatusResponse)
def auth_status():
    settings = get_settings()
    store = get_token_store(settings.TOKEN_STORE_TYPE, settings.TOKEN_STORE_PATH)
    token_data = store.load()

    if not token_data:
        return AuthStatusResponse(authorized=False)

    return AuthStatusResponse(
        authorized=True,
        scopes=token_data.get("scopes", []),
        token_expiry=token_data.get("expiry"),
    )


@router.post("/revoke", response_model=RevokeResponse)
def auth_revoke():
    settings = get_settings()
    store = get_token_store(settings.TOKEN_STORE_TYPE, settings.TOKEN_STORE_PATH)
    store.clear()
    get_logger().info("OAuth tokens revoked/cleared")
    return RevokeResponse(revoked=True)
