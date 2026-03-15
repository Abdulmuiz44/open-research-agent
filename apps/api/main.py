"""FastAPI application entrypoint for Open Research Agent."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from src.core.config import get_settings
from src.core.logging import configure_logging_from_settings, get_logger
from src.data.schemas import HealthResponse, ResearchRunCreateRequest, ResearchRunResponse
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
        message="Run completed with bounded HTTP-first fetch and browser fallback recovery.",
        search_queries=output.search_queries,
        discovered_sources=len(output.discovered_sources),
        fetched_sources=fetched_success,
        fetched_http_count=output.fetched_http_count,
        fetched_browser_count=output.fetched_browser_count,
        fallback_trigger_count=output.fallback_trigger_count,
        extracted_documents=len(output.extracted_documents),
        extraction_status_summary=output.extraction_status_summary,
        artifact_paths=output.artifact_paths,
    )


@app.get("/runs/{run_id}", response_model=ResearchRunResponse)
def get_research_run(run_id: str) -> ResearchRunResponse:
    """Fetch run metadata by run ID."""
    run = storage.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return ResearchRunResponse(
        run_id=run.id,
        objective=run.objective,
        status=run.status,
        created_at=run.created_at,
        updated_at=run.updated_at,
        message="Run metadata retrieved from local storage.",
        artifact_paths=storage.get_run_artifact_paths(run_id),
    )
