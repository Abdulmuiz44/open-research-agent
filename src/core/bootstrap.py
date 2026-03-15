"""Shared startup bootstrap for API and CLI entrypoints."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.core.config import Settings, get_settings
from src.core.exceptions import ConfigurationError
from src.core.logging import configure_logging_from_settings, get_logger


@dataclass(frozen=True)
class BootstrapState:
    """Runtime bootstrap state shared by API and CLI."""

    settings: Settings
    writable_paths: tuple[Path, ...]


def _ensure_writable(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    test_file = path / ".ora-write-check"
    try:
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
    except OSError as exc:
        raise ConfigurationError(f"Path '{path}' is not writable: {exc}") from exc


def prepare_local_paths(settings: Settings) -> tuple[Path, ...]:
    """Create and validate required runtime directories."""
    writable_paths: list[Path] = []
    for path in settings.output_directories():
        _ensure_writable(path)
        writable_paths.append(path)
    return tuple(writable_paths)


def bootstrap_runtime(*, service_mode: str | None = None) -> BootstrapState:
    """Initialize config, logging, and startup validation once for a process."""
    settings = get_settings()
    if service_mode:
        settings.service_mode = service_mode

    configure_logging_from_settings(settings)
    settings.validate_runtime()
    writable_paths = prepare_local_paths(settings)

    logger = get_logger("ora.bootstrap")
    logger.info(
        "startup complete | app=%s env=%s mode=%s api=%s:%s data_dir=%s",
        settings.app_name,
        settings.environment,
        settings.service_mode,
        settings.api_host,
        settings.api_port,
        settings.data_dir,
    )

    return BootstrapState(settings=settings, writable_paths=writable_paths)
