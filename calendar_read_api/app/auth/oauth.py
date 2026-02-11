from __future__ import annotations

from google_auth_oauthlib.flow import Flow

from app.config import get_settings


def build_flow(redirect_uri: str | None = None) -> Flow:
    settings = get_settings()
    if redirect_uri is None:
        redirect_uri = f"{settings.BASE_URL}/auth/callback"

    flow = Flow.from_client_secrets_file(
        settings.GOOGLE_OAUTH_CLIENT_SECRET_PATH,
        scopes=settings.SCOPES,
        redirect_uri=redirect_uri,
    )
    return flow
