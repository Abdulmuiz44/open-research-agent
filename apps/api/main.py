"""FastAPI application entrypoint for Open Research Agent."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from src import __version__
from src.core.config import get_settings
from src.core.logging import configure_logging_from_settings, get_logger
from src.data.schemas import (
    HealthResponse,
    ReadyResponse,
    ResearchRunCreateRequest,
    ResearchRunResponse,
    RunArtifactsResponse,
    RunListResponse,
)
from src.data.storage import LocalStorageStub
from src.workflows.run_research import RunResearchInput, run_research_workflow

settings = get_settings()
configure_logging_from_settings(settings)
logger = get_logger("ora.api")
storage = LocalStorageStub()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("api startup | env=%s", settings.environment)
    yield


app = FastAPI(title="Open Research Agent API", version=__version__, lifespan=lifespan)


def _build_run_response(*, output=None, run=None, search_queries=None, artifact_count=0, artifact_dir=None, report_path=None, message=None) -> ResearchRunResponse:
    if output is not None:
        run = output.run
        search_queries = output.search_queries
        metrics = output.run_metrics
        artifact_count = len(output.artifact_paths)
        artifact_dir = output.artifact_dir
        report_path = output.artifact_refs.get("report")
    else:
        metrics = None
    source_count = metrics.source_count if metrics else 0
    fetched_count = metrics.fetched_count if metrics else 0
    extracted_count = metrics.extracted_count if metrics else 0
    findings_count = metrics.findings_count if metrics else 0
    return ResearchRunResponse(
        run_id=run.id,
        query=run.objective,
        objective=run.objective,
        status=run.status,
        created_at=run.created_at,
        updated_at=run.updated_at,
        message=message,
        search_queries=search_queries or [],
        source_count=source_count,
        fetched_count=fetched_count,
        extracted_count=extracted_count,
        findings_count=findings_count,
        artifact_count=artifact_count,
        artifact_dir=artifact_dir,
        report_path=report_path,
        discovered_sources=source_count,
        fetched_sources=fetched_count,
        extracted_documents=extracted_count,
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(app_name=settings.app_name, environment=settings.environment, version=__version__)


@app.get("/ready", response_model=ReadyResponse)
def ready() -> ReadyResponse:
    """Return service readiness status."""
    return ReadyResponse(runs_dir=str(settings.runs_dir.resolve()))


@app.post("/runs", response_model=ResearchRunResponse)
def start_research_run(payload: ResearchRunCreateRequest) -> ResearchRunResponse:
    """Execute a bounded local research run and return run summary."""
    output = run_research_workflow(
        RunResearchInput(objective=payload.objective, constraints=payload.constraints, max_sources=payload.max_sources),
        storage=storage,
    )
    return _build_run_response(output=output, message="Run completed with bounded local discovery/fetch/extract flow.")


@app.get("/runs", response_model=RunListResponse)
def list_runs() -> RunListResponse:
    """List all known runs from local storage."""
    return RunListResponse(runs=[_build_run_response(run=run, message="Run metadata retrieved from local storage.") for run in storage.list_runs()])


@app.get("/runs/{run_id}", response_model=ResearchRunResponse)
def get_research_run(run_id: str) -> ResearchRunResponse:
    """Fetch run metadata by run ID."""
    run = storage.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    artifacts = storage.list_run_artifacts(run_id)
    refs = storage.get_run_artifact_refs(run_id)
    return _build_run_response(
        run=run,
        artifact_count=len(artifacts),
        artifact_dir=str((settings.runs_dir / run_id).resolve()),
        report_path=refs.get("report"),
        message="Run metadata retrieved from local storage.",
    )


@app.get("/runs/{run_id}/artifacts", response_model=RunArtifactsResponse)
def get_run_artifacts(run_id: str) -> RunArtifactsResponse:
    """List artifact references for a run."""
    run = storage.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return RunArtifactsResponse(run_id=run_id, artifact_paths=storage.list_run_artifacts(run_id), artifact_refs=storage.get_run_artifact_refs(run_id))
