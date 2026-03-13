"""Environment-driven application configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for Open Research Agent."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ORA_",
        extra="ignore",
        env_file_encoding="utf-8",
    )

    app_name: str = "open-research-agent"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    api_host: str = "127.0.0.1"
    api_port: int = 8000

    runs_dir: Path = Path("outputs/runs")
    artifacts_dir: Path = Path("outputs/artifacts")

    default_model: str = "gpt-4o-mini"
    planner_model: str = "gpt-4o-mini"
    analysis_model: str = "gpt-4o-mini"

    openai_api_key: str | None = Field(default=None, repr=False)
    anthropic_api_key: str | None = Field(default=None, repr=False)
    search_api_key: str | None = Field(default=None, repr=False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache application settings for process lifetime."""
    return Settings()
