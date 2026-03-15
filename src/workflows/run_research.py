"""Research workflow orchestration for bounded local runs."""

from __future__ import annotations

import asyncio

from pydantic import BaseModel, Field

from src.core.config import get_settings
from src.agents.reporter import ReporterAgent
from src.data.models import (
    AnalysisArtifact,
    ArtifactKind,
    CandidateSource,
    ExtractedDocument,
    FetchedDocument,
    ResearchPlan,
    ResearchRun,
    RunStatus,
    Source,
)
from src.data.storage import LocalStorageStub, StorageBackend
from src.search.provider import build_search_provider
from src.search.queries import build_queries
from src.web.crawler import Crawler
from src.web.extractor import Extractor


class RunResearchInput(BaseModel):
    """Inputs required to kick off a bounded research workflow run."""

    objective: str = Field(min_length=3)
    constraints: list[str] = Field(default_factory=list)
    max_sources: int = Field(default=10, ge=1, le=100)


class RunResearchOutput(BaseModel):
    """Top-level workflow output with stage artifacts."""

    run: ResearchRun
    plan: ResearchPlan
    search_queries: list[str]
    discovered_sources: list[CandidateSource]
    fetched_documents: list[FetchedDocument]
    extracted_documents: list[ExtractedDocument]
    analysis_artifacts: list[AnalysisArtifact]
    report_markdown: str
    artifact_dir: str
    artifact_paths: list[str]
    artifact_refs: dict[str, str]


def initialize_run(payload: RunResearchInput) -> ResearchRun:
    """Create initial run metadata before stage orchestration."""
    return ResearchRun(objective=payload.objective)


def _build_plan(payload: RunResearchInput) -> ResearchPlan:
    objectives = [payload.objective, *payload.constraints]
    return ResearchPlan(
        objective=payload.objective,
        research_objectives=objectives[:3],
        source_budget=min(payload.max_sources, get_settings().max_sources_per_run),
    )


def run_research_workflow(
    payload: RunResearchInput,
    storage: StorageBackend | None = None,
) -> RunResearchOutput:
    """Execute bounded local discovery, fetch, extract, and simple analysis/reporting."""
    backend = storage or LocalStorageStub()
    run = backend.create_run(initialize_run(payload))
    backend.update_run_status(run.id, RunStatus.RUNNING)

    try:
        plan = _build_plan(payload)
        queries = build_queries(plan)

        provider = build_search_provider(get_settings())
        crawler = Crawler(provider)
        discovered = crawler.discover(run.id, queries)
        fetched = asyncio.run(crawler.fetch(discovered))

        extractor = Extractor()
        extracted = [extractor.extract(doc) for doc in fetched if doc.success and (doc.raw_html or doc.text)]

        backend.save_artifact_json(
            run.id,
            "manifest.json",
            {
                "run_id": run.id,
                "objective": run.objective,
                "status": "running",
                "created_at": run.created_at.isoformat(),
            },
        )
        plan_path = backend.save_artifact_json(run.id, "plan.json", plan.model_dump(mode="json"))
        sources_path = backend.save_artifact_json(
            run.id,
            "sources.json",
            [source.model_dump(mode="json") for source in discovered],
        )
        fetched_path = backend.save_artifact_json(
            run.id,
            "fetched/documents.json",
            [
                {
                    "source_id": doc.source_id,
                    "requested_url": str(doc.requested_url),
                    "final_url": str(doc.final_url) if doc.final_url else None,
                    "status_code": doc.status_code,
                    "success": doc.success,
                    "error": doc.error,
                    "fetched_at": doc.fetched_at.isoformat(),
                }
                for doc in fetched
            ],
        )

        for source in discovered:
            backend.save_source(
                Source(
                    id=source.id,
                    run_id=source.run_id,
                    url=source.url,
                    domain=source.domain,
                    title=source.title,
                )
            )
        for document in extracted:
            backend.save_extracted_document(document)

        extracted_path = backend.save_artifact_json(
            run.id,
            "extracted/documents.json",
            [document.model_dump(mode="json") for document in extracted],
        )

        fetched_success = len([d for d in fetched if d.success])
        summary = f"Discovered {len(discovered)} sources, fetched {fetched_success}, extracted {len(extracted)} documents."
        artifact = AnalysisArtifact(
            run_id=run.id,
            kind=ArtifactKind.SUMMARY,
            summary=summary,
            evidence_ids=[doc.id for doc in extracted],
        )
        backend.save_analysis_artifact_metadata(artifact)

        reporter = ReporterAgent()
        report = reporter.build_report(
            run_id=run.id,
            objective=run.objective,
            extracted_documents=extracted,
            analysis_artifacts=[artifact],
            sources=discovered,
            generated_at=run.updated_at,
        )
        report_markdown = report.markdown
        report_path = backend.save_artifact_markdown(run.id, "report/report.md", report_markdown)

        run = backend.update_run_status(run.id, RunStatus.COMPLETED)
        final_result_path = backend.save_artifact_json(
            run.id,
            "analysis/final_result.json",
            {
                "run_id": run.id,
                "status": run.status.value,
                "query": run.objective,
                "discovered_sources": len(discovered),
                "fetched_sources": fetched_success,
                "extracted_documents": len(extracted),
                "artifact_count": len(backend.list_run_artifacts(run.id)),
                "report_path": report_path,
            },
        )
        backend.save_artifact_json(
            run.id,
            "manifest.json",
            {
                "run_id": run.id,
                "objective": run.objective,
                "status": run.status.value,
                "created_at": run.created_at.isoformat(),
                "updated_at": run.updated_at.isoformat(),
                "paths": {
                    "plan": plan_path,
                    "sources": sources_path,
                    "fetched": fetched_path,
                    "extracted": extracted_path,
                    "report": report_path,
                    "final_result": final_result_path,
                },
            },
        )

        artifact_refs = backend.get_run_artifact_refs(run.id)
        artifact_refs.update(
            {
                "plan": plan_path,
                "sources": sources_path,
                "fetched": fetched_path,
                "extracted": extracted_path,
                "report": report_path,
                "final_result": final_result_path,
            }
        )
        return RunResearchOutput(
            run=run,
            plan=plan,
            search_queries=queries,
            discovered_sources=discovered,
            fetched_documents=fetched,
            extracted_documents=extracted,
            analysis_artifacts=[artifact],
            report_markdown=report_markdown,
            artifact_dir=str((backend.base_dir / run.id).resolve()) if isinstance(backend, LocalStorageStub) else str((get_settings().runs_dir / run.id).resolve()),
            artifact_paths=backend.list_run_artifacts(run.id),
            artifact_refs=artifact_refs,
        )
    except Exception as exc:
        backend.update_run_status(run.id, RunStatus.FAILED, error_message=str(exc))
        raise
