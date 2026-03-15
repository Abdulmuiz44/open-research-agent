"""Research workflow orchestration for bounded local runs."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from src.agents.analyst import AnalystAgent
from src.agents.reporter import ReporterAgent
from src.core.config import get_settings
from src.core.exceptions import WorkflowError
from src.data.models import (
    AnalysisArtifact,
    ArtifactKind,
    CandidateSource,
    ExtractedDocument,
    FetchedDocument,
    ResearchPlan,
    ResearchRun,
    RunMetrics,
    RunStatus,
    Source,
)
from src.data.storage import LocalStorageStub, StorageBackend
from src.search.provider import build_search_provider
from src.search.queries import build_queries
from src.web.crawler import Crawler
from src.web.extractor import Extractor


class RunResearchInput(BaseModel):
    objective: str = Field(min_length=3)
    constraints: list[str] = Field(default_factory=list)
    max_sources: int = Field(default=10, ge=1, le=100)


class RunResearchOutput(BaseModel):
    run: ResearchRun
    plan: ResearchPlan
    search_queries: list[str]
    discovered_sources: list[CandidateSource]
    fetched_documents: list[FetchedDocument]
    extracted_documents: list[ExtractedDocument]
    analysis_artifacts: list[AnalysisArtifact]
    run_metrics: RunMetrics
    report_markdown: str
    artifact_dir: str
    artifact_paths: list[str]
    artifact_refs: dict[str, str]


def initialize_run(payload: RunResearchInput) -> ResearchRun:
    return ResearchRun(objective=payload.objective)


def _build_plan(payload: RunResearchInput) -> ResearchPlan:
    objectives = [payload.objective, *payload.constraints]
    return ResearchPlan(
        objective=payload.objective,
        research_objectives=objectives[:3],
        source_budget=min(payload.max_sources, get_settings().max_sources_per_run),
    )


def run_research_workflow(payload: RunResearchInput, storage: StorageBackend | None = None) -> RunResearchOutput:
    backend = storage or LocalStorageStub()
    run = backend.create_run(initialize_run(payload))
    run = backend.update_run_status(run.id, RunStatus.RUNNING)

    try:
        plan = _build_plan(payload)
        queries = build_queries(plan)
        provider = build_search_provider(get_settings())
        crawler = Crawler(provider)
        discovered = crawler.discover(run.id, queries)
        fetched = asyncio.run(crawler.fetch(discovered))

        extractor = Extractor()
        extracted = [extractor.extract(doc) for doc in fetched if doc.success and (doc.raw_html or doc.text)]
        analysis = AnalystAgent().analyze_documents(extracted)
        metrics = RunMetrics(
            source_count=len(discovered),
            fetched_count=len([doc for doc in fetched if doc.success]),
            extracted_count=len(extracted),
            findings_count=len(analysis.findings),
        )

        artifact_dir = str((Path(getattr(backend, "base_dir", get_settings().runs_dir)) / run.id).resolve())
        backend.save_artifact_json(
            run.id,
            "manifest.json",
            {
                "run_id": run.id,
                "status": RunStatus.RUNNING.value,
                "query": run.objective,
                "artifact_dir": artifact_dir,
                "created_at": run.created_at.isoformat(),
                "updated_at": run.updated_at.isoformat(),
            },
        )
        plan_path = backend.save_plan_artifact(run.id, plan)
        sources_path = backend.save_artifact_json(run.id, "sources.json", [source.model_dump(mode="json") for source in discovered])
        fetched_path = backend.save_artifact_json(
            run.id,
            "fetched/documents.json",
            [
                {
                    "source_id": doc.source_id,
                    "requested_url": str(doc.requested_url),
                    "final_url": str(doc.final_url) if doc.final_url else None,
                    "status": "success" if doc.success else "failed",
                    "status_code": doc.status_code,
                    "error": doc.error,
                    "fetched_at": doc.fetched_at.isoformat(),
                }
                for doc in fetched
            ],
        )
        for fetched_document in fetched:
            backend.save_fetched_metadata(fetched_document)
        for source in discovered:
            backend.save_source_metadata(Source(id=source.id, run_id=source.run_id, url=source.url, domain=source.domain, title=source.title))
        for document in extracted:
            backend.save_extracted_document_metadata(document)
        extracted_path = backend.save_artifact_json(run.id, "extracted/documents.json", [document.model_dump(mode="json") for document in extracted])

        findings_path = backend.save_artifact_json(run.id, "analysis/findings.json", [finding.model_dump(mode="json") for finding in analysis.findings])
        themes_path = backend.save_artifact_json(run.id, "analysis/themes.json", [theme.model_dump(mode="json") for theme in analysis.themes])
        contradictions_path = backend.save_artifact_json(run.id, "analysis/contradictions.json", [item.model_dump(mode="json") for item in analysis.contradictions])
        analysis_summary_path = backend.save_artifact_json(run.id, "analysis/analysis_summary.json", analysis.summary.model_dump(mode="json"))

        analysis_artifacts = [
            AnalysisArtifact(run_id=run.id, kind=ArtifactKind.SUMMARY, summary=analysis.summary.summary, evidence_ids=[doc.id for doc in extracted]),
            AnalysisArtifact(run_id=run.id, kind=ArtifactKind.FINDINGS, summary=f"{len(analysis.findings)} findings", evidence_ids=[doc.id for doc in extracted]),
        ]
        for artifact in analysis_artifacts:
            backend.save_analysis_artifact_metadata(artifact)

        report = ReporterAgent().build_report(
            run_id=run.id,
            objective=run.objective,
            extracted_documents=extracted,
            analysis_artifacts=analysis_artifacts,
            sources=discovered,
            generated_at=datetime.now(UTC),
        )
        report_path = backend.save_artifact_markdown(run.id, "report/report.md", report.markdown)
        backend.save_report_artifact_metadata(run.id, report_path)

        run = backend.update_run_status(run.id, RunStatus.COMPLETED)
        final_result_path = backend.save_artifact_json(
            run.id,
            "analysis/final_result.json",
            {
                "run_id": run.id,
                "status": run.status.value,
                "query": run.objective,
                "source_count": metrics.source_count,
                "fetched_count": metrics.fetched_count,
                "extracted_count": metrics.extracted_count,
                "findings_count": metrics.findings_count,
                "artifact_dir": artifact_dir,
                "report_path": report_path,
                "created_at": run.created_at.isoformat(),
                "updated_at": run.updated_at.isoformat(),
                "discovered_sources": metrics.source_count,
                "fetched_sources": metrics.fetched_count,
                "extracted_documents": metrics.extracted_count,
            },
        )
        backend.save_artifact_json(
            run.id,
            "manifest.json",
            {
                "run_id": run.id,
                "status": run.status.value,
                "query": run.objective,
                "source_count": metrics.source_count,
                "fetched_count": metrics.fetched_count,
                "extracted_count": metrics.extracted_count,
                "findings_count": metrics.findings_count,
                "artifact_dir": artifact_dir,
                "report_path": report_path,
                "created_at": run.created_at.isoformat(),
                "updated_at": run.updated_at.isoformat(),
                "paths": {
                    "plan": plan_path,
                    "sources": sources_path,
                    "fetched": fetched_path,
                    "extracted": extracted_path,
                    "findings": findings_path,
                    "themes": themes_path,
                    "contradictions": contradictions_path,
                    "analysis_summary": analysis_summary_path,
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
                "findings": findings_path,
                "themes": themes_path,
                "contradictions": contradictions_path,
                "analysis_summary": analysis_summary_path,
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
            analysis_artifacts=analysis_artifacts,
            run_metrics=metrics,
            report_markdown=report.markdown,
            artifact_dir=artifact_dir,
            artifact_paths=backend.list_run_artifacts(run.id),
            artifact_refs=artifact_refs,
        )
    except Exception as exc:  # pragma: no cover
        backend.update_run_status(run.id, RunStatus.FAILED, error_message=str(exc))
        raise WorkflowError(f"Run {run.id} failed: {exc}") from exc
