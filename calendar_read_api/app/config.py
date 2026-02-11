from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    GOOGLE_OAUTH_CLIENT_SECRET_PATH: str = os.getenv(
        "GOOGLE_OAUTH_CLIENT_SECRET_PATH", ""
    )
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    TOKEN_STORE_TYPE: str = os.getenv("TOKEN_STORE_TYPE", "dev_file")
    TOKEN_STORE_PATH: str = os.getenv("TOKEN_STORE_PATH", "./token.json")
    DEFAULT_TIMEZONE: str = os.getenv("DEFAULT_TIMEZONE", "America/Denver")
    MAX_LOOKAHEAD_DAYS: int = int(os.getenv("MAX_LOOKAHEAD_DAYS", "30"))
    MAX_LOOKBACK_DAYS: int = int(os.getenv("MAX_LOOKBACK_DAYS", "30"))
    MAX_EVENTS_DEFAULT: int = int(os.getenv("MAX_EVENTS_DEFAULT", "250"))
    MAX_EVENTS_HARD_CAP: int = 2500
    ALLOW_CLAMPING: bool = os.getenv("ALLOW_CLAMPING", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    SCOPES: list[str] = [
        "https://www.googleapis.com/auth/calendar.events.readonly",
        "https://www.googleapis.com/auth/calendar.freebusy",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
