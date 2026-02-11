from __future__ import annotations

import logging
import sys

from app.config import get_settings


def setup_logging() -> logging.Logger:
    settings = get_settings()
    logger = logging.getLogger("calendar_read_api")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logger.level)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger("calendar_read_api")
