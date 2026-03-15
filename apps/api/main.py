"""FastAPI application entrypoint for Open Research Agent."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

from src.core.config import get_settings
from src.core.logging import configure_logging_from_settings, get_logger
from src.data.schemas import (
    HealthResponse,
    ResearchRunCreateRequest,
    ResearchRunListResponse,
    ResearchRunResponse,
    RunArtifactsResponse,
)
from src.data.storage import LocalPersistentStorage
from src.workflows.run_research import RunResearchInput, run_research_workflow

settings = get_settings()
configure_logging_from_settings(settings)
logger = get_logger("ora.api")
storage = LocalPersistentStorage(base_dir=settings.runs_dir)
app = FastAPI(title="Open Research Agent API", version="0.1.0")


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact_summary(artifact_paths: list[str]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for relative_path in artifact_paths:
        bucket = relative_path.split("/", 1)[0]
        summary[bucket] = summary.get(bucket, 0) + 1
    return summary


def _run_counts(run_id: str, refs: dict[str, str], artifact_paths: list[str]) -> tuple[int, int, int]:
    run_dir = settings.runs_dir / run_id

    source_count = 0
    sources_payload = _load_json(run_dir / "sources.json")
    if isinstance(sources_payload, list):
        source_count = len(sources_payload)
    elif artifact_paths:
        source_count = len([path for path in artifact_paths if path.startswith("sources/")])

    extracted_count = 0
    extracted_payload = _load_json(run_dir / "extracted" / "documents.json")
    if isinstance(extracted_payload, list):
        extracted_count = len(extracted_payload)
    else:
        extracted_count = len([path for path in artifact_paths if path.startswith("extracted/") and path.endswith(".json")])

    finding_count = len([key for key in refs if key.startswith("analysis_")])
    if finding_count == 0:
        finding_count = len([path for path in artifact_paths if path.startswith("analysis/summary_")])

    return source_count, extracted_count, finding_count


def _build_run_response(run_id: str, message: str, search_queries: list[str] | None = None) -> ResearchRunResponse:
    run = storage.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    artifact_paths = storage.list_run_artifacts(run_id)
    refs = storage.get_run_artifact_refs(run_id)
    source_count, extracted_count, finding_count = _run_counts(run_id, refs, artifact_paths)
    return ResearchRunResponse(
        run_id=run.id,
        objective=run.objective,
        status=run.status,
        created_at=run.created_at,
        updated_at=run.updated_at,
        message=message,
        search_queries=search_queries or [],
        discovered_sources=source_count,
        extracted_documents=extracted_count,
        finding_count=finding_count,
        artifact_count=len(artifact_paths),
        artifact_dir=str((settings.runs_dir / run_id).resolve()),
        artifact_summary=_artifact_summary(artifact_paths),
        report_path=refs.get("report"),
    )


@app.on_event("startup")
def startup() -> None:
    """Log API startup context."""
    logger.info("api startup | env=%s", settings.environment)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(app_name=settings.app_name, environment=settings.environment)


@app.post("/runs", response_model=ResearchRunResponse)
def start_research_run(payload: ResearchRunCreateRequest) -> ResearchRunResponse:
    """Execute a bounded local research run and return run summary."""
    output = run_research_workflow(
        RunResearchInput(
            objective=payload.objective,
            constraints=payload.constraints,
            max_sources=payload.max_sources,
        ),
        storage=storage,
    )
    response = _build_run_response(
        run_id=output.run.id,
        message="Run completed with bounded real discovery/fetch/extract flow.",
        search_queries=output.search_queries,
    )
    response.fetched_sources = len([item for item in output.fetched_documents if item.success])
    return response


@app.get("/runs", response_model=ResearchRunListResponse)
def list_research_runs(limit: int = Query(default=20, ge=1, le=100)) -> ResearchRunListResponse:
    """List recent runs from persistent local storage."""
    runs = [
        _build_run_response(run_id=run.id, message="Run metadata retrieved from local storage.")
        for run in storage.list_runs(limit=limit)
    ]
    return ResearchRunListResponse(runs=runs)


@app.get("/runs/{run_id}", response_model=ResearchRunResponse)
def get_research_run(run_id: str) -> ResearchRunResponse:
    """Fetch run metadata by run ID."""
    return _build_run_response(run_id=run_id, message="Run metadata retrieved from local storage.")


@app.get("/runs/{run_id}/artifacts", response_model=RunArtifactsResponse)
def get_run_artifacts(run_id: str) -> RunArtifactsResponse:
    """List artifact references for a run."""
    run = storage.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return RunArtifactsResponse(
        run_id=run_id,
        artifact_paths=storage.list_run_artifacts(run_id),
        artifact_refs=storage.get_run_artifact_refs(run_id),
    )
