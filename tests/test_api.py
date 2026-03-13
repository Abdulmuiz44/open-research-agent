"""API smoke tests for FastAPI app lifecycle."""

from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def test_health_route() -> None:
    """Health route should return OK status and metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app_name"]


def test_create_run_route_placeholder() -> None:
    """Run creation endpoint should create metadata placeholder."""
    payload = {"objective": "test objective", "constraints": [], "max_sources": 5}
    response = client.post("/runs", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "created"
    assert body["run_id"]
    assert "not implemented yet" in body["message"].lower()


def test_get_run_route() -> None:
    """Run retrieval should return existing placeholder run metadata."""
    created = client.post("/runs", json={"objective": "retrieve me"}).json()
    run_id = created["run_id"]

    response = client.get(f"/runs/{run_id}")
    assert response.status_code == 200
    assert response.json()["run_id"] == run_id
