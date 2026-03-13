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


def test_run_route_not_implemented() -> None:
    """Run creation endpoint should signal scaffold placeholder state."""
    payload = {"objective": "test objective", "constraints": [], "max_sources": 5}
    response = client.post("/runs", json=payload)
    assert response.status_code == 501
