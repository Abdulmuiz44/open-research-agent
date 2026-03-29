"""CLI smoke tests for Typer entrypoint."""

from __future__ import annotations

from typer.testing import CliRunner

from apps.cli.main import app


runner = CliRunner()


def test_cli_help() -> None:
    """CLI should render help output."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Open Research Agent" in result.stdout


def test_cli_research_get_list_artifacts() -> None:
    research = runner.invoke(app, ["research", "test objective"])
    assert research.exit_code == 0
    assert "run_id:" in research.stdout
    assert "artifact_dir:" in research.stdout

    run_id_line = next(line for line in research.stdout.splitlines() if line.startswith("run_id:"))
    run_id = run_id_line.split(":", maxsplit=1)[1].strip()

    get_result = runner.invoke(app, ["get", run_id])
    assert get_result.exit_code == 0
    assert f"run_id: {run_id}" in get_result.stdout

    list_result = runner.invoke(app, ["list"])
    assert list_result.exit_code == 0
    assert run_id in list_result.stdout

    artifacts_result = runner.invoke(app, ["artifacts", run_id])
    assert artifacts_result.exit_code == 0
    assert "artifact_count:" in artifacts_result.stdout
