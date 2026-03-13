"""Typer CLI entrypoint for Open Research Agent."""

from __future__ import annotations

import typer

from src.core.config import get_settings
from src.core.logging import configure_logging_from_settings, get_logger

app = typer.Typer(help="Open Research Agent command line interface.")


@app.callback()
def main() -> None:
    """Initialize config and logging for every CLI invocation."""
    settings = get_settings()
    configure_logging_from_settings(settings)


@app.command()
def health() -> None:
    """Report local runtime health and configuration summary."""
    settings = get_settings()
    logger = get_logger("ora.cli")
    logger.info("health check completed")
    typer.echo(
        f"ok | app={settings.app_name} env={settings.environment} api={settings.api_host}:{settings.api_port}"
    )


@app.command()
def research(objective: str) -> None:
    """Run bounded research workflow (placeholder)."""
    _ = objective
    typer.echo("research command is not implemented yet.", err=True)
    raise typer.Exit(code=1)


@app.command()
def fetch(url: str) -> None:
    """Fetch content for a URL (placeholder)."""
    _ = url
    typer.echo("fetch command is not implemented yet.", err=True)
    raise typer.Exit(code=1)


@app.command()
def analyze(run_id: str) -> None:
    """Analyze artifacts for an existing run (placeholder)."""
    _ = run_id
    typer.echo("analyze command is not implemented yet.", err=True)
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
