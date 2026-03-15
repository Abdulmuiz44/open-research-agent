"""Environment-driven application configuration and startup validation."""

from __future__ import annotations

import ipaddress
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
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

    service_mode: str = "api"
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    data_dir: Path = Path("outputs")
    runs_dir: Path = Path("outputs/runs")
    artifacts_dir: Path = Path("outputs/artifacts")
    reports_dir: Path = Path("outputs/reports")
    metadata_dir: Path = Path("outputs/metadata")

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

    openai_api_key: str | None = Field(default=None, repr=False)
    anthropic_api_key: str | None = Field(default=None, repr=False)
    search_api_key: str | None = Field(default=None, repr=False)

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        allowed = {"development", "test", "staging", "production"}
        normalized = value.strip().lower()
        if normalized not in allowed:
            raise ValueError(f"ORA_ENVIRONMENT must be one of {sorted(allowed)}, got '{value}'.")
        return normalized

    @field_validator("service_mode")
    @classmethod
    def validate_service_mode(cls, value: str) -> str:
        allowed = {"api", "cli"}
        normalized = value.strip().lower()
        if normalized not in allowed:
            raise ValueError(f"ORA_SERVICE_MODE must be one of {sorted(allowed)}, got '{value}'.")
        return normalized

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        normalized = value.strip().upper()
        if normalized not in allowed:
            raise ValueError(f"ORA_LOG_LEVEL must be one of {sorted(allowed)}, got '{value}'.")
        return normalized

    @field_validator("api_host")
    @classmethod
    def validate_api_host(cls, value: str) -> str:
        host = value.strip()
        if not host:
            raise ValueError("ORA_API_HOST cannot be empty.")
        if host != "0.0.0.0":
            try:
                ipaddress.ip_address(host)
            except ValueError:
                if "." not in host and host != "localhost":
                    raise ValueError("ORA_API_HOST must be a valid IP address, 'localhost', or a valid hostname.")
        return host

    @field_validator("api_port")
    @classmethod
    def validate_api_port(cls, value: int) -> int:
        if value < 1 or value > 65535:
            raise ValueError("ORA_API_PORT must be between 1 and 65535.")
        return value

    @field_validator("data_dir", "runs_dir", "artifacts_dir", "reports_dir", "metadata_dir", mode="before")
    @classmethod
    def expand_path(cls, value: str | Path) -> Path:
        return Path(value).expanduser()

    @model_validator(mode="after")
    def validate_runtime_limits(self) -> "Settings":
        if str(self.runs_dir) == "outputs/runs":
            self.runs_dir = self.data_dir / "runs"
        if str(self.artifacts_dir) == "outputs/artifacts":
            self.artifacts_dir = self.data_dir / "artifacts"
        if str(self.reports_dir) == "outputs/reports":
            self.reports_dir = self.data_dir / "reports"
        if str(self.metadata_dir) == "outputs/metadata":
            self.metadata_dir = self.data_dir / "metadata"

        if self.request_timeout_seconds <= 0:
            raise ConfigurationError("ORA_REQUEST_TIMEOUT_SECONDS must be greater than 0")
        if self.request_retries < 0:
            raise ConfigurationError("ORA_REQUEST_RETRIES must be 0 or greater")
        if self.max_fetch_per_run > self.max_sources_per_run:
            raise ConfigurationError("ORA_MAX_FETCH_PER_RUN cannot exceed ORA_MAX_SOURCES_PER_RUN")
        if self.runs_dir == self.artifacts_dir:
            raise ConfigurationError("ORA_RUNS_DIR and ORA_ARTIFACTS_DIR must be different paths")

        required_for_provider: dict[str, tuple[str | None, str]] = {
            "serpapi": (self.search_api_key, "ORA_SEARCH_API_KEY"),
            "tavily": (self.search_api_key, "ORA_SEARCH_API_KEY"),
        }
        key_check = required_for_provider.get(self.search_provider.lower())
        if key_check and not key_check[0]:
            raise ConfigurationError(f"Search provider '{self.search_provider}' requires setting {key_check[1]}.")
        return self

    def output_directories(self) -> tuple[Path, ...]:
        return (self.data_dir, self.runs_dir, self.artifacts_dir, self.reports_dir, self.metadata_dir)

    def validate_runtime(self) -> None:
        Settings.model_validate(self.model_dump())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache application settings for process lifetime."""
    return Settings()


def clear_settings_cache() -> None:
    """Clear cached settings. Primarily useful for tests."""
    get_settings.cache_clear()
