"""Typer CLI entrypoint for Open Research Agent."""

from __future__ import annotations

import typer

from src.core.bootstrap import BootstrapState, bootstrap_runtime
from src.core.exceptions import ConfigurationError
from src.core.logging import get_logger
from src.workflows.run_research import RunResearchInput, run_research_workflow

app = typer.Typer(help="Open Research Agent command line interface.")
_bootstrap_state: BootstrapState | None = None


@app.callback()
def main() -> None:
    """Initialize config, logging, and startup validation for every CLI invocation."""
    global _bootstrap_state
    try:
        _bootstrap_state = bootstrap_runtime(service_mode="cli")
    except ConfigurationError as exc:
        raise typer.BadParameter(f"Startup validation failed: {exc}") from exc


@app.command()
def health() -> None:
    """Report local runtime health and configuration summary."""
    state = _bootstrap_state or bootstrap_runtime(service_mode="cli")
    logger = get_logger("ora.cli")
    logger.info("health check completed")
    typer.echo(
        f"ok | app={state.settings.app_name} env={state.settings.environment} "
        f"api={state.settings.api_host}:{state.settings.api_port} data_dir={state.settings.data_dir}"
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
