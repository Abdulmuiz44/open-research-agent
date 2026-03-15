"""FastAPI application entrypoint for Open Research Agent."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from src.core.config import get_settings
from src.core.logging import configure_logging_from_settings, get_logger
from src.data.schemas import HealthResponse, ResearchRunCreateRequest, ResearchRunResponse, RunArtifactsResponse
from src.data.storage import LocalStorageStub
from src.workflows.run_research import RunResearchInput, run_research_workflow

settings = get_settings()
configure_logging_from_settings(settings)
logger = get_logger("ora.api")
storage = LocalStorageStub()
app = FastAPI(title="Open Research Agent API", version="0.1.0")


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
    fetched_success = len([item for item in output.fetched_documents if item.success])
    return ResearchRunResponse(
        run_id=output.run.id,
        objective=output.run.objective,
        status=output.run.status,
        created_at=output.run.created_at,
        updated_at=output.run.updated_at,
        message="Run completed with bounded real discovery/fetch/extract flow.",
        search_queries=output.search_queries,
        discovered_sources=len(output.discovered_sources),
        fetched_sources=fetched_success,
        extracted_documents=len(output.extracted_documents),
        artifact_count=len(output.artifact_paths),
        artifact_dir=output.artifact_dir,
        report_path=output.artifact_refs.get("report"),
    )


@app.get("/runs/{run_id}", response_model=ResearchRunResponse)
def get_research_run(run_id: str) -> ResearchRunResponse:
    """Fetch run metadata by run ID."""
    run = storage.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    artifacts = storage.get_run_artifacts(run_id)
    report_path = str((settings.runs_dir / run_id / "report" / "report.md").resolve()) if "report/report.md" in artifacts else None
    return ResearchRunResponse(
        run_id=run.id,
        objective=run.objective,
        status=run.status,
        created_at=run.created_at,
        updated_at=run.updated_at,
        message="Run metadata retrieved from local storage.",
        artifact_count=len(artifacts),
        artifact_dir=str((settings.runs_dir / run_id).resolve()),
        report_path=report_path,
    )


@app.get("/runs/{run_id}/artifacts", response_model=RunArtifactsResponse)
def get_run_artifacts(run_id: str) -> RunArtifactsResponse:
    """List artifact references for a run."""
    run = storage.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return RunArtifactsResponse(
        run_id=run_id,
        artifact_paths=storage.get_run_artifacts(run_id),
        artifact_refs={},
    )
