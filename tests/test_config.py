"""Configuration loading tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from src.core.config import Settings
from src.core.exceptions import ConfigurationError


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.app_name == "open-research-agent"
    assert settings.api_port == 8000
    assert settings.default_model
    assert settings.reports_dir == Path("outputs/reports")


def test_settings_init_override() -> None:
    settings = Settings(environment="test", debug=True, api_port=9001, data_dir=Path("tmp/data"))
    assert settings.environment == "test"
    assert settings.debug is True
    assert settings.api_port == 9001
    assert settings.runs_dir == Path("tmp/data/runs")


def test_invalid_port_fails_validation() -> None:
    with pytest.raises(ValidationError):
        Settings(api_port=99999)


def test_invalid_environment_fails_validation() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="invalid")


def test_provider_requires_api_key() -> None:
    settings = Settings(search_provider="serpapi", search_api_key=None)
    with pytest.raises(ConfigurationError):
        settings.validate_runtime()
