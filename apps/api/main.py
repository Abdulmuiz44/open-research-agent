"""FastAPI application entrypoint for Open Research Agent."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

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
storage = LocalStorageStub(base_dir=settings.runs_dir)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("api startup | env=%s", settings.environment)
    yield


app = FastAPI(title="Open Research Agent API", version=__version__, lifespan=lifespan)


def _read_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact_summary(artifact_paths: list[str]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for relative_path in artifact_paths:
        bucket = relative_path.split("/", 1)[0]
        summary[bucket] = summary.get(bucket, 0) + 1
    return summary


def _persisted_counts(run_id: str, refs: dict[str, str], artifact_paths: list[str]) -> tuple[int, int, int, int]:
    final_result = _read_json(settings.runs_dir / run_id / "analysis" / "final_result.json")
    if isinstance(final_result, dict):
        source_count = int(final_result.get("source_count", final_result.get("discovered_sources", 0)))
        fetched_count = int(final_result.get("fetched_count", final_result.get("fetched_sources", 0)))
        extracted_count = int(final_result.get("extracted_count", final_result.get("extracted_documents", 0)))
        findings_count = int(final_result.get("findings_count", final_result.get("finding_count", 0)))
        return source_count, fetched_count, extracted_count, findings_count

    source_count = len([path for path in artifact_paths if path.startswith("sources/")])
    fetched_count = len([path for path in artifact_paths if path.startswith("fetched/") and path.endswith(".json") and path != "fetched/documents.json"])
    extracted_count = len([path for path in artifact_paths if path.startswith("extracted/") and path.endswith(".json") and path != "extracted/documents.json"])
    findings_count = len([key for key in refs if key.startswith("analysis_")])
    return source_count, fetched_count, extracted_count, findings_count


def _build_run_response(*, output=None, run=None, search_queries=None, artifact_count=0, artifact_dir=None, report_path=None, artifact_summary=None, message=None) -> ResearchRunResponse:
    if output is not None:
        run = output.run
        search_queries = output.search_queries
        metrics = output.run_metrics
        artifact_count = len(output.artifact_paths)
        artifact_dir = output.artifact_dir
        report_path = output.artifact_refs.get("report")
        artifact_summary = _artifact_summary(output.artifact_paths)
        source_count = metrics.source_count
        fetched_count = metrics.fetched_count
        extracted_count = metrics.extracted_count
        findings_count = metrics.findings_count
    else:
        source_count, fetched_count, extracted_count, findings_count = _persisted_counts(
            run.id,
            storage.get_run_artifact_refs(run.id),
            storage.list_run_artifacts(run.id),
        )
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
        artifact_summary=artifact_summary or {},
        report_path=report_path,
        discovered_sources=source_count,
        fetched_sources=fetched_count,
        extracted_documents=extracted_count,
        finding_count=findings_count,
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(app_name=settings.app_name, environment=settings.environment, version=__version__)


@app.get("/ready", response_model=ReadyResponse)
def ready() -> ReadyResponse:
    return ReadyResponse(runs_dir=str(settings.runs_dir.resolve()))


@app.post("/runs", response_model=ResearchRunResponse)
def start_research_run(payload: ResearchRunCreateRequest) -> ResearchRunResponse:
    output = run_research_workflow(
        RunResearchInput(objective=payload.objective, constraints=payload.constraints, max_sources=payload.max_sources),
        storage=storage,
    )
    return _build_run_response(output=output, message="Run completed with bounded local discovery/fetch/extract flow.")


@app.get("/runs", response_model=RunListResponse)
def list_runs() -> RunListResponse:
    runs = []
    for run in storage.list_runs():
        artifact_paths = storage.list_run_artifacts(run.id)
        refs = storage.get_run_artifact_refs(run.id)
        runs.append(
            _build_run_response(
                run=run,
                artifact_count=len(artifact_paths),
                artifact_dir=str((settings.runs_dir / run.id).resolve()),
                artifact_summary=_artifact_summary(artifact_paths),
                report_path=refs.get("report"),
                message="Run metadata retrieved from local storage.",
            )
        )
    return RunListResponse(runs=runs)


@app.get("/runs/{run_id}", response_model=ResearchRunResponse)
def get_research_run(run_id: str) -> ResearchRunResponse:
    run = storage.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    artifacts = storage.list_run_artifacts(run_id)
    refs = storage.get_run_artifact_refs(run_id)
    return _build_run_response(
        run=run,
        artifact_count=len(artifacts),
        artifact_dir=str((settings.runs_dir / run_id).resolve()),
        artifact_summary=_artifact_summary(artifacts),
        report_path=refs.get("report"),
        message="Run metadata retrieved from local storage.",
    )


@app.get("/runs/{run_id}/artifacts", response_model=RunArtifactsResponse)
def get_run_artifacts(run_id: str) -> RunArtifactsResponse:
    run = storage.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return RunArtifactsResponse(run_id=run_id, artifact_paths=storage.list_run_artifacts(run_id), artifact_refs=storage.get_run_artifact_refs(run_id))
