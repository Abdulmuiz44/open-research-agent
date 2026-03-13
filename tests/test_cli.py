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


def test_cli_health() -> None:
    """CLI health command should return success output."""
    result = runner.invoke(app, ["health"])
    assert result.exit_code == 0
    assert "ok | app=" in result.stdout


def test_cli_placeholder_commands_fail() -> None:
    """Deferred commands should return a clear non-zero placeholder status."""
    result = runner.invoke(app, ["research", "test objective"])
    assert result.exit_code == 1
    assert "not implemented yet" in result.stdout
