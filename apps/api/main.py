"""FastAPI application entrypoint for Open Research Agent."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException

from src.data.schemas import ResearchRunCreateRequest, ResearchRunResponse
from src.data.storage import LocalStorage
from src.workflows.run_research import RunResearchInput, run_research_workflow

app = FastAPI(title="Open Research Agent API", version="0.1.0")
storage = LocalStorage()


@app.get("/health")
def health() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok"}


@app.post("/runs", response_model=ResearchRunResponse)
def start_research_run(payload: ResearchRunCreateRequest) -> ResearchRunResponse:
    """Start a new deterministic local research run."""
    output = run_research_workflow(
        RunResearchInput(objective=payload.objective, constraints=payload.constraints, max_sources=payload.max_sources),
        storage=storage,
    )
    return ResearchRunResponse(
        run_id=output.run.id,
        objective=output.run.objective,
        status=output.run.status,
        created_at=output.run.created_at,
        artifact_count=len(output.artifact_paths),
        artifact_dir=str((Path(storage.runs_dir) / output.run.id).resolve()),
        report_path=output.artifact_refs.get("report"),
    )


@app.get("/runs/{run_id}", response_model=ResearchRunResponse)
def get_research_run(run_id: str) -> ResearchRunResponse:
    """Fetch research run details by run ID."""
    run = storage.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    refs = storage.get_run_artifact_refs(run_id)
    return ResearchRunResponse(
        run_id=run.id,
        objective=run.objective,
        status=run.status,
        created_at=run.created_at,
        artifact_count=len(storage.list_run_artifacts(run_id)),
        artifact_dir=str((Path(storage.runs_dir) / run.id).resolve()),
        report_path=refs.get("report"),
    )
