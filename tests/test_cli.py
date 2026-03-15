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


def test_cli_research_success(monkeypatch) -> None:
    workflow_module.get_settings.cache_clear()
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: StubSearchProvider())
    result = runner.invoke(app, ["research", "test objective"])
    assert result.exit_code == 0
    assert "run_id:" in result.stdout
    assert "status:" in result.stdout
    assert "artifact_output_dir:" in result.stdout
    assert "report_artifact_path:" in result.stdout
