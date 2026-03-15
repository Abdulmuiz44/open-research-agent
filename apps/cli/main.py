"""Typer CLI entrypoint for Open Research Agent."""

from __future__ import annotations

import typer

from src import __version__
from src.core.config import get_settings
from src.core.logging import configure_logging_from_settings, get_logger
from src.data.storage import LocalStorageStub
from src.workflows.run_research import RunResearchInput, run_research_workflow

app = typer.Typer(help="Open Research Agent command line interface.")
storage = LocalStorageStub()


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
    typer.echo(f"ok | app={settings.app_name} env={settings.environment} version={__version__} api={settings.api_host}:{settings.api_port}")


@app.command()
def research(objective: str, max_sources: int = 6) -> None:
    """Run bounded research workflow."""
    output = run_research_workflow(RunResearchInput(objective=objective, max_sources=max_sources), storage=storage)

    typer.echo(f"run_id: {output.run.id}")
    typer.echo(f"status: {output.run.status.value}")
    typer.echo(f"query: {output.run.objective}")
    typer.echo(f"source_count: {output.run_metrics.source_count}")
    typer.echo(f"fetched_count: {output.run_metrics.fetched_count}")
    typer.echo(f"extracted_count: {output.run_metrics.extracted_count}")
    typer.echo(f"findings_count: {output.run_metrics.findings_count}")
    typer.echo(f"artifact_dir: {output.artifact_dir}")
    typer.echo(f"report_path: {output.artifact_refs.get('report', 'not_generated')}")


@app.command(name="get")
def get_run(run_id: str) -> None:
    """Get run metadata for an existing run ID."""
    run = storage.get_run(run_id)
    if run is None:
        typer.echo(f"error: run_id {run_id} not found", err=True)
        raise typer.Exit(code=1)
    refs = storage.get_run_artifact_refs(run_id)
    typer.echo(f"run_id: {run.id}")
    typer.echo(f"status: {run.status.value}")
    typer.echo(f"query: {run.objective}")
    typer.echo(f"artifact_count: {len(storage.list_run_artifacts(run_id))}")
    typer.echo(f"artifact_dir: {(get_settings().runs_dir / run_id).resolve()}")
    typer.echo(f"report_path: {refs.get('report', 'not_generated')}")


@app.command(name="list")
def list_runs() -> None:
    """List local runs."""
    runs = storage.list_runs()
    if not runs:
        typer.echo("no runs found")
        return
    for run in runs:
        typer.echo(f"{run.id} | {run.status.value} | {run.objective}")


@app.command()
def artifacts(run_id: str) -> None:
    """List artifact paths and refs for a run."""
    run = storage.get_run(run_id)
    if run is None:
        typer.echo(f"error: run_id {run_id} not found", err=True)
        raise typer.Exit(code=1)
    refs = storage.get_run_artifact_refs(run_id)
    paths = storage.list_run_artifacts(run_id)
    typer.echo(f"run_id: {run_id}")
    typer.echo(f"artifact_count: {len(paths)}")
    for path in paths:
        typer.echo(f"- {path}")
    if refs:
        typer.echo("artifact_refs:")
        for key, value in sorted(refs.items()):
            typer.echo(f"  {key}: {value}")


if __name__ == "__main__":
    app()
