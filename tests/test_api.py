"""API smoke tests for FastAPI app lifecycle."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from apps.api import main as api_main
from apps.api.main import app
from src.core.config import Settings
from src.data.storage import SQLiteStorageBackend
from src.search.provider import StubSearchProvider
from src.workflows import run_research as workflow_module


client = TestClient(app)


def test_health_route() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app_name"]
    assert payload["version"]


def test_ready_route() -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_create_run_route_executes_workflow(monkeypatch) -> None:
    workflow_module.get_settings.cache_clear()
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: StubSearchProvider())
    payload = {"objective": "test objective", "constraints": [], "max_sources": 5}
    response = client.post("/runs", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["run_id"]
    assert body["query"] == "test objective"
    assert "source_count" in body
    assert "artifact_dir" in body


def test_list_runs_route(monkeypatch) -> None:
    workflow_module.get_settings.cache_clear()
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: StubSearchProvider())
    client.post("/runs", json={"objective": "list me"})
    response = client.get("/runs")
    assert response.status_code == 200
    payload = response.json()
    assert payload["runs"]


def test_get_run_route(monkeypatch) -> None:
    workflow_module.get_settings.cache_clear()
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: StubSearchProvider())
    created = client.post("/runs", json={"objective": "retrieve me"}).json()
    run_id = created["run_id"]

    response = client.get(f"/runs/{run_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == run_id
    assert "artifact_count" in body


def test_get_run_route_reads_persisted_records(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "api.db"
    runs_dir = tmp_path / "runs"
    sqlite_storage = SQLiteStorageBackend(db_path=db_path, base_dir=runs_dir)

    workflow_module.get_settings.cache_clear()
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: StubSearchProvider())
    monkeypatch.setattr(workflow_module, "get_settings", lambda: Settings(runs_dir=runs_dir))
    monkeypatch.setattr(api_main, "storage", sqlite_storage)

    created = client.post("/runs", json={"objective": "persisted api retrieval"}).json()
    run_id = created["run_id"]

    monkeypatch.setattr(api_main, "storage", SQLiteStorageBackend(db_path=db_path, base_dir=runs_dir))
    response = client.get(f"/runs/{run_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == run_id
    assert body["status"] == "completed"
    assert body["artifact_count"] > 0


def test_get_run_artifacts_route(monkeypatch) -> None:
    workflow_module.get_settings.cache_clear()
    monkeypatch.setattr(workflow_module, "build_search_provider", lambda _settings: StubSearchProvider())
    created = client.post("/runs", json={"objective": "artifacts please"}).json()
    run_id = created["run_id"]

    response = client.get(f"/runs/{run_id}/artifacts")
    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == run_id
    assert payload["artifact_paths"]
