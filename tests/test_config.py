"""Configuration loading tests."""

from __future__ import annotations

from src.core.config import Settings


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
