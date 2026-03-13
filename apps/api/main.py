"""FastAPI application entrypoint for Open Research Agent."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from src.core.config import get_settings
from src.core.logging import configure_logging_from_settings, get_logger
from src.data.models import ResearchRun
from src.data.schemas import HealthResponse, ResearchRunCreateRequest, ResearchRunResponse
from src.data.storage import LocalStorageStub

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
    """Create run metadata placeholder without executing workflow stages."""
    run = storage.create_run(ResearchRun(objective=payload.objective))
    return ResearchRunResponse(
        run_id=run.id,
        objective=run.objective,
        status=run.status,
        created_at=run.created_at,
        updated_at=run.updated_at,
        message="Run created. Workflow execution is not implemented yet.",
    )


@app.get("/runs/{run_id}", response_model=ResearchRunResponse)
def get_research_run(run_id: str) -> ResearchRunResponse:
    """Fetch run metadata placeholder by run ID."""
    run = storage.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return ResearchRunResponse(
        run_id=run.id,
        objective=run.objective,
        status=run.status,
        created_at=run.created_at,
        updated_at=run.updated_at,
        message="Run metadata only. Workflow execution is not implemented yet.",
    )
