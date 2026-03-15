"""Logging helpers for consistent application logging."""

from __future__ import annotations

import logging

from src.core.config import Settings

DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


class _ContextFilter(logging.Filter):
    """Inject shared runtime context fields into every log record."""

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._environment = settings.environment
        self._service_mode = settings.service_mode

    def filter(self, record: logging.LogRecord) -> bool:
        record.environment = self._environment
        record.service_mode = self._service_mode
        return True


def configure_logging(*, level: str = "INFO", settings: Settings | None = None) -> None:
    """Configure root logger in an idempotent, production-friendly way."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        logging.basicConfig(level=log_level, format=DEFAULT_FORMAT)
    else:
        root_logger.setLevel(log_level)
        for handler in root_logger.handlers:
            handler.setLevel(log_level)

    if settings:
        context_filter = _ContextFilter(settings)
        for handler in root_logger.handlers:
            handler.addFilter(context_filter)


def configure_logging_from_settings(settings: Settings) -> None:
    """Configure logging from application settings."""
    configure_logging(level=settings.log_level, settings=settings)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger instance."""
    return logging.getLogger(name)
