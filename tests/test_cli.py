"""CLI smoke tests for Typer entrypoint."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from apps.cli import main as cli_main
from apps.cli.main import app
from src.core.config import Settings
from src.data.storage import SQLiteStorageBackend
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


def test_cli_inspect_by_id_output_fields(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "cli.db"
    runs_dir = tmp_path / "runs"
    sqlite_storage = SQLiteStorageBackend(db_path=db_path, base_dir=runs_dir)

    workflow_module.get_settings.cache_clear()
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: StubSearchProvider())
    monkeypatch.setattr(workflow_module, "get_settings", lambda: Settings(runs_dir=runs_dir))
    monkeypatch.setattr(cli_main, "storage", sqlite_storage)

    research = runner.invoke(app, ["research", "inspect retrieval objective"])
    assert research.exit_code == 0
    run_id_line = next(line for line in research.stdout.splitlines() if line.startswith("run_id:"))
    run_id = run_id_line.split(":", maxsplit=1)[1].strip()

    monkeypatch.setattr(cli_main, "storage", SQLiteStorageBackend(db_path=db_path, base_dir=runs_dir))
    inspect_result = runner.invoke(app, ["inspect", run_id])

    assert inspect_result.exit_code == 0
    assert f"run_id: {run_id}" in inspect_result.stdout
    assert "objective:" in inspect_result.stdout
    assert "status:" in inspect_result.stdout
    assert "artifact_count:" in inspect_result.stdout
    assert "report_path:" in inspect_result.stdout
