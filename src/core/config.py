"""Environment-driven application configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src import __version__
from src.core.exceptions import ConfigurationError


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

    search_provider: str = "duckduckgo_html"
    search_endpoint: str = "https://duckduckgo.com/html/"
    request_timeout_seconds: float = 10.0
    request_retries: int = 2
    user_agent: str = f"open-research-agent/{__version__} (+https://example.local)"
    max_sources_per_run: int = 8
    max_fetch_per_run: int = 6

    browser_fallback_enabled: bool = True
    browser_fallback_min_text_chars: int = 200
    browser_fallback_timeout_seconds: float = 8.0
    browser_fallback_wait_seconds: float = 1.5

    openai_api_key: str | None = Field(default=None, repr=False)
    anthropic_api_key: str | None = Field(default=None, repr=False)
    search_api_key: str | None = Field(default=None, repr=False)

    @model_validator(mode="after")
    def validate_runtime_limits(self) -> "Settings":
        """Validate settings needed for bounded MVP runtime behavior."""
        if self.request_timeout_seconds <= 0:
            raise ConfigurationError("ORA_REQUEST_TIMEOUT_SECONDS must be greater than 0")
        if self.request_retries < 0:
            raise ConfigurationError("ORA_REQUEST_RETRIES must be 0 or greater")
        if self.max_fetch_per_run > self.max_sources_per_run:
            raise ConfigurationError("ORA_MAX_FETCH_PER_RUN cannot exceed ORA_MAX_SOURCES_PER_RUN")
        if self.runs_dir == self.artifacts_dir:
            raise ConfigurationError("ORA_RUNS_DIR and ORA_ARTIFACTS_DIR must be different paths")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache application settings for process lifetime."""
    return Settings()
