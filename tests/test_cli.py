"""CLI smoke tests for Typer entrypoint."""

from __future__ import annotations

from typer.testing import CliRunner

from apps.cli.main import app
from src.search.provider import StubSearchProvider
from src.workflows import run_research as workflow_module


runner = CliRunner()


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Open Research Agent" in result.stdout


def test_cli_health() -> None:
    result = runner.invoke(app, ["health"])
    assert result.exit_code == 0
    assert "ok | app=" in result.stdout


def test_cli_research_get_list_artifacts(monkeypatch) -> None:
    workflow_module.get_settings.cache_clear()
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: StubSearchProvider())

    research = runner.invoke(app, ["research", "test objective"])
    assert research.exit_code == 0
    assert "run_id:" in research.stdout
    assert "source_count:" in research.stdout
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
