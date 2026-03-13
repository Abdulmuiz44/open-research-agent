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
