"""Bootstrap startup behavior tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core.bootstrap import bootstrap_runtime, prepare_local_paths
from src.core.config import clear_settings_cache
from src.core.exceptions import ConfigurationError


def test_prepare_local_paths_creates_directories(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORA_DATA_DIR", str(tmp_path / "data-root"))
    clear_settings_cache()

    state = bootstrap_runtime(service_mode="cli")

    for path in state.writable_paths:
        assert path.exists()
        assert path.is_dir()


def test_bootstrap_fails_on_missing_provider_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORA_SEARCH_PROVIDER", "serpapi")
    monkeypatch.delenv("ORA_SEARCH_API_KEY", raising=False)
    clear_settings_cache()

    with pytest.raises(ConfigurationError):
        bootstrap_runtime(service_mode="api")


def test_prepare_local_paths_handles_custom_directories(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORA_DATA_DIR", str(tmp_path / "root"))
    monkeypatch.setenv("ORA_RUNS_DIR", str(tmp_path / "explicit-runs"))
    clear_settings_cache()

    state = bootstrap_runtime(service_mode="api")
    assert Path(tmp_path / "explicit-runs") in state.writable_paths
    prepare_local_paths(state.settings)
