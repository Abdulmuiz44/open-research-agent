"""Typer CLI entrypoint for Open Research Agent."""

from __future__ import annotations

import typer

from src.core.config import get_settings
from src.core.logging import configure_logging_from_settings, get_logger
from src.workflows.run_research import RunResearchInput, run_research_workflow

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
def research(objective: str, max_sources: int = 6) -> None:
    """Run bounded research workflow."""
    output = run_research_workflow(RunResearchInput(objective=objective, max_sources=max_sources))
    fetched_success = len([item for item in output.fetched_documents if item.success])

    typer.echo(f"run_id: {output.run.id}")
    typer.echo(f"status: {output.run.status}")
    typer.echo(f"queries: {', '.join(output.search_queries)}")
    typer.echo(f"discovered_sources: {len(output.discovered_sources)}")
    typer.echo(f"fetched_sources: {fetched_success}")
    typer.echo(f"extracted_documents: {len(output.extracted_documents)}")


@app.command()
def fetch(url: str) -> None:
    """Fetch command remains intentionally narrow."""
    _ = url
    typer.echo("fetch command is intentionally limited; use research for full flow.")


@app.command()
def analyze(run_id: str) -> None:
    """Analyze command remains intentionally narrow."""
    _ = run_id
    typer.echo("analyze command is intentionally limited; use research for full flow.")


if __name__ == "__main__":
    app()
