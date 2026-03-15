"""Typer CLI entrypoint for Open Research Agent."""

from __future__ import annotations

import json

import typer

from src.core.config import get_settings
from src.core.logging import configure_logging_from_settings, get_logger
from src.data.storage import LocalStorageStub
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
    typer.echo(f"discovered_sources: {len(output.discovered_sources)}")
    typer.echo(f"fetched_sources: {fetched_success}")
    typer.echo(f"extracted_documents: {len(output.extracted_documents)}")
    typer.echo(f"artifact_output_dir: {output.artifact_dir}")
    typer.echo(f"report_artifact_path: {output.artifact_refs.get('report', 'not_generated')}")


@app.command()
def inspect(run_id: str) -> None:
    """Inspect a saved run by run ID from the storage backend."""
    storage = LocalStorageStub()
    run = storage.get_run(run_id)
    if run is None:
        typer.echo(f"run {run_id} not found")
        raise typer.Exit(code=1)

    run_dir = get_settings().runs_dir / run.id
    sources_count = 0
    sources_path = run_dir / "sources.json"
    if sources_path.exists():
        sources_count = len(json.loads(sources_path.read_text(encoding="utf-8")))

    extracted_count = 0
    extracted_path = run_dir / "extracted/documents.json"
    if extracted_path.exists():
        extracted_count = len(json.loads(extracted_path.read_text(encoding="utf-8")))

    finding_count = 0
    final_result_path = run_dir / "analysis/final_result.json"
    if final_result_path.exists():
        final_result = json.loads(final_result_path.read_text(encoding="utf-8"))
        if final_result.get("status") == "completed":
            finding_count = 1

    artifact_refs = storage.get_run_artifact_refs(run.id)

    typer.echo(f"run id: {run.id}")
    typer.echo(f"status: {run.status.value}")
    typer.echo(f"query/objective: {run.objective}")
    typer.echo(f"source count: {sources_count}")
    typer.echo(f"extracted document count: {extracted_count}")
    typer.echo(f"finding count: {finding_count}")
    typer.echo(f"artifact directory: {str(run_dir.resolve())}")
    typer.echo(f"report path: {artifact_refs.get('report', str((run_dir / 'report/report.md').resolve()))}")


@app.command("runs")
def list_runs(limit: int = 10) -> None:
    """List recent runs from local storage."""
    storage = LocalStorageStub()
    runs = storage.list_runs(limit=limit)
    if not runs:
        typer.echo("no runs found")
        return

    for run in runs:
        typer.echo(f"{run.id} | {run.status.value} | {run.objective}")


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
