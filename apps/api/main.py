"""FastAPI application entrypoint for Open Research Agent."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from src.core.bootstrap import BootstrapState, bootstrap_runtime
from src.core.exceptions import ConfigurationError
from src.core.logging import get_logger
from src.data.schemas import (
    HealthResponse,
    ReadinessResponse,
    ResearchRunCreateRequest,
    ResearchRunResponse,
)
from src.data.storage import LocalStorageStub
from src.workflows.run_research import RunResearchInput, run_research_workflow

logger = get_logger("ora.api")
storage = LocalStorageStub()
app = FastAPI(title="Open Research Agent API", version="0.1.0")
_bootstrap_state: BootstrapState | None = None


@app.on_event("startup")
def startup() -> None:
    """Run one-time startup bootstrap and fail fast on invalid config."""
    global _bootstrap_state
    try:
        _bootstrap_state = bootstrap_runtime(service_mode="api")
    except ConfigurationError:
        logger.exception("api startup failed due to invalid configuration")
        raise


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service liveness status."""
    state = _bootstrap_state or bootstrap_runtime(service_mode="api")
    return HealthResponse(app_name=state.settings.app_name, environment=state.settings.environment)


@app.get("/ready", response_model=ReadinessResponse)
def ready() -> ReadinessResponse:
    """Return service readiness status based on local startup dependencies."""
    state = _bootstrap_state
    if state is None:
        return ReadinessResponse(
            status="not_ready",
            app_name="open-research-agent",
            environment="unknown",
            service_mode="api",
            writable_paths=[],
        )

    return ReadinessResponse(
        status="ready",
        app_name=state.settings.app_name,
        environment=state.settings.environment,
        service_mode=state.settings.service_mode,
        writable_paths=[str(path) for path in state.writable_paths],
    )


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
        message="Run completed with bounded real discovery/fetch flow.",
        search_queries=output.search_queries,
        discovered_sources=len(output.discovered_sources),
        fetched_sources=fetched_success,
        extracted_documents=len(output.extracted_documents),
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
    )
