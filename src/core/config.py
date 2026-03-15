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
    storage_db_path: Path = Path("outputs/metadata.sqlite3")

    default_model: str = "gpt-4o-mini"
    planner_model: str = "gpt-4o-mini"
    analysis_model: str = "gpt-4o-mini"

    search_provider: str = "duckduckgo_html"
    search_endpoint: str = "https://duckduckgo.com/html/"
    request_timeout_seconds: float = 10.0
    request_retries: int = 2
    user_agent: str = "open-research-agent/0.1 (+https://example.local)"
    max_sources_per_run: int = 8
    max_fetch_per_run: int = 6

    openai_api_key: str | None = Field(default=None, repr=False)
    anthropic_api_key: str | None = Field(default=None, repr=False)
    search_api_key: str | None = Field(default=None, repr=False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache application settings for process lifetime."""
    return Settings()
