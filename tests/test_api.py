"""API smoke tests for FastAPI app lifecycle."""

from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app
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
    assert body["search_queries"]
    assert "source_count" in body
    assert "artifact_count" in body
    assert "artifact_dir" in body
    assert "artifact_summary" in body
    assert body["report_path"]


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
    assert "discovered_sources" in body
    assert "extracted_documents" in body
    assert "finding_count" in body


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
