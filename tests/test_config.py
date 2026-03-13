"""Configuration loading tests."""

from __future__ import annotations

from src.core.config import Settings


def test_settings_defaults() -> None:
    """Settings should load sensible local defaults."""
    settings = Settings()
    assert settings.app_name == "open-research-agent"
    assert settings.api_port == 8000
    assert settings.default_model


def test_settings_env_override() -> None:
    """Environment variables should override defaults."""
    settings = Settings(ORA_ENVIRONMENT="test", ORA_DEBUG="true", ORA_API_PORT=9001)
    assert settings.environment == "test"
    assert settings.debug is True
    assert settings.api_port == 9001
