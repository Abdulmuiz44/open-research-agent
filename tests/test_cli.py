"""CLI smoke tests for Typer entrypoint."""

from __future__ import annotations

from pathlib import Path

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


def test_cli_inspect_by_run_id(monkeypatch, tmp_path: Path) -> None:
    workflow_module.get_settings.cache_clear()
    monkeypatch.setenv("ORA_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: StubSearchProvider())

    research_result = runner.invoke(app, ["research", "inspect objective"])
    run_id_line = [line for line in research_result.stdout.splitlines() if line.startswith("run_id:")][0]
    run_id = run_id_line.split(":", maxsplit=1)[1].strip()

    workflow_module.get_settings.cache_clear()
    result = runner.invoke(app, ["inspect", run_id])
    assert result.exit_code == 0
    assert "run id:" in result.stdout
    assert "status:" in result.stdout
    assert "query/objective:" in result.stdout
    assert "source count:" in result.stdout
    assert "extracted document count:" in result.stdout
    assert "finding count:" in result.stdout
    assert "artifact directory:" in result.stdout
    assert "report path:" in result.stdout


def test_cli_runs_lists_recent(monkeypatch, tmp_path: Path) -> None:
    workflow_module.get_settings.cache_clear()
    monkeypatch.setenv("ORA_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: StubSearchProvider())

    first = runner.invoke(app, ["research", "first objective"])
    second = runner.invoke(app, ["research", "second objective"])

    first_id = [line for line in first.stdout.splitlines() if line.startswith("run_id:")][0].split(":", maxsplit=1)[1].strip()
    second_id = [line for line in second.stdout.splitlines() if line.startswith("run_id:")][0].split(":", maxsplit=1)[1].strip()

    workflow_module.get_settings.cache_clear()
    result = runner.invoke(app, ["runs", "--limit", "2"])

    assert result.exit_code == 0
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 2
    assert second_id in lines[0]
    assert first_id in lines[1]
