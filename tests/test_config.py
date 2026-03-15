"""Configuration loading tests."""

from __future__ import annotations

import pytest

from src.core.config import Settings
from src.core.exceptions import ConfigurationError


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.app_name == "open-research-agent"
    assert settings.api_port == 8000
    assert settings.default_model


def test_settings_init_override() -> None:
    settings = Settings(environment="test", debug=True, api_port=9001)
    assert settings.environment == "test"
    assert settings.debug is True
    assert settings.api_port == 9001


def test_settings_validation_errors() -> None:
    with pytest.raises(ConfigurationError):
        Settings(request_timeout_seconds=0)
    with pytest.raises(ConfigurationError):
        Settings(max_sources_per_run=2, max_fetch_per_run=3)
