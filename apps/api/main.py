"""FastAPI application entrypoint for Open Research Agent."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from src.data.schemas import ResearchRunCreateRequest, ResearchRunResponse

app = FastAPI(title="Open Research Agent API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok"}


@app.post("/runs", response_model=ResearchRunResponse)
def start_research_run(payload: ResearchRunCreateRequest) -> ResearchRunResponse:
    """Start a new research run (placeholder endpoint)."""
    # TODO: Wire request to workflow runner and persistent storage.
    raise HTTPException(status_code=501, detail="Not implemented")


@app.get("/runs/{run_id}", response_model=ResearchRunResponse)
def get_research_run(run_id: str) -> ResearchRunResponse:
    """Fetch research run details by run ID (placeholder endpoint)."""
    # TODO: Load run state from storage adapter.
    raise HTTPException(status_code=501, detail=f"Run {run_id} retrieval not implemented")
