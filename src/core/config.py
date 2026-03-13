"""Environment-driven application configuration."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for Open Research Agent."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="ORA_", extra="ignore")

    app_name: str = "open-research-agent"
    environment: str = "development"
    log_level: str = "INFO"

    openai_api_key: str | None = Field(default=None, description="API key for model providers.")
    search_api_key: str | None = Field(default=None, description="API key for search provider.")

    default_model: str = "gpt-4o-mini"
    planner_model: str = "gpt-4o-mini"
    analysis_model: str = "gpt-4o-mini"

    runs_dir: Path = Path("outputs/runs")
    artifacts_dir: Path = Path("outputs/artifacts")
    database_url: str = "duckdb:///outputs/ora.duckdb"

    max_sources: int = 10
    request_timeout_seconds: float = 20.0
    enable_browser_fallback: bool = True


def get_settings() -> Settings:
    """Load and return application settings."""
    # TODO: Add memoization/caching once runtime lifecycle is in place.
    return Settings()
