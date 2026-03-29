"""API smoke tests for FastAPI app lifecycle."""

from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def test_health_route() -> None:
    """Health route should return OK status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_get_run_route() -> None:
    payload = {"objective": "test objective", "constraints": [], "max_sources": 5}
    create = client.post("/runs", json=payload)
    assert create.status_code == 200
    body = create.json()
    assert body["status"] == "completed"
    assert body["run_id"]
    assert body["report_path"]

    get_resp = client.get(f"/runs/{body['run_id']}")
    assert get_resp.status_code == 200
    loaded = get_resp.json()
    assert loaded["run_id"] == body["run_id"]
    assert loaded["status"] == "completed"
