"""Logging helpers for consistent application logging."""

from __future__ import annotations

import logging

from src.core.config import Settings


DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging(*, level: str = "INFO") -> None:
    """Configure root logger in an idempotent, production-friendly way."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        logging.basicConfig(level=log_level, format=DEFAULT_FORMAT)
    else:
        root_logger.setLevel(log_level)
        for handler in root_logger.handlers:
            handler.setLevel(log_level)


def configure_logging_from_settings(settings: Settings) -> None:
    """Configure logging from application settings."""
    configure_logging(level=settings.log_level)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger instance."""
    return logging.getLogger(name)
