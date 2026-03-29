"""Typer CLI entrypoint for Open Research Agent."""

from __future__ import annotations

import typer

from src.data.storage import LocalStorage
from src.workflows.run_research import RunResearchInput, run_research_workflow

app = typer.Typer(help="Open Research Agent command line interface.")
storage = LocalStorage()


@app.command()
def research(objective: str, max_sources: int = 5) -> None:
    """Run a bounded research workflow for an objective."""
    output = run_research_workflow(RunResearchInput(objective=objective, max_sources=max_sources), storage=storage)
    typer.echo(f"run_id: {output.run.id}")
    typer.echo(f"status: {output.run.status}")
    typer.echo(f"artifact_dir: {output.artifact_dir}")
    typer.echo(f"report_path: {output.artifact_refs.get('report', 'not_generated')}")


@app.command(name="get")
def get_run(run_id: str) -> None:
    """Show a run summary by ID."""
    run = storage.get_run(run_id)
    if run is None:
        typer.echo(f"error: run_id {run_id} not found", err=True)
        raise typer.Exit(code=1)
    refs = storage.get_run_artifact_refs(run_id)
    typer.echo(f"run_id: {run.id}")
    typer.echo(f"status: {run.status}")
    typer.echo(f"objective: {run.objective}")
    typer.echo(f"artifact_count: {len(storage.list_run_artifacts(run_id))}")
    typer.echo(f"report_path: {refs.get('report', 'not_generated')}")


@app.command(name="list")
def list_runs() -> None:
    """List local runs."""
    runs = storage.list_runs()
    if not runs:
        typer.echo("no runs found")
        return
    for run in runs:
        typer.echo(f"{run.id} | {run.status} | {run.objective}")


@app.command()
def artifacts(run_id: str) -> None:
    """List artifacts for a run."""
    run = storage.get_run(run_id)
    if run is None:
        typer.echo(f"error: run_id {run_id} not found", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"run_id: {run_id}")
    paths = storage.list_run_artifacts(run_id)
    typer.echo(f"artifact_count: {len(paths)}")
    for path in paths:
        typer.echo(f"- {path}")


if __name__ == "__main__":
    app()
