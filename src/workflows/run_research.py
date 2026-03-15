"""Research workflow orchestration for bounded local runs."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from pydantic import BaseModel, Field

from src.agents.analyst import AnalystAgent
from src.agents.reporter import ReporterAgent
from src.core.config import get_settings
from src.data.models import (
    AnalysisArtifact,
    AnalysisResult,
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
    analysis: AnalysisResult
    analysis_artifacts: list[AnalysisArtifact]
    report_markdown: str
    artifact_dir: str
    report_path: str


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


def _save_analysis_artifacts(run_id: str, analysis: AnalysisResult) -> tuple[str, str]:
    settings = get_settings()
    run_dir = Path(settings.runs_dir) / run_id
    analysis_dir = run_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    (analysis_dir / "findings.json").write_text(
        json.dumps([item.model_dump(mode="json") for item in analysis.findings], indent=2),
        encoding="utf-8",
    )
    (analysis_dir / "themes.json").write_text(
        json.dumps([item.model_dump(mode="json") for item in analysis.themes], indent=2),
        encoding="utf-8",
    )
    (analysis_dir / "contradictions.json").write_text(
        json.dumps([item.model_dump(mode="json") for item in analysis.contradictions], indent=2),
        encoding="utf-8",
    )
    (analysis_dir / "analysis_summary.json").write_text(
        json.dumps(analysis.summary.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )

    return str(analysis_dir), str(run_dir / "report.md")


def run_research_workflow(
    payload: RunResearchInput,
    storage: StorageBackend | None = None,
) -> RunResearchOutput:
    """Execute bounded local discovery, fetch, extract, deterministic analysis, and reporting."""
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

        analysis = AnalystAgent().analyze_documents(extracted)

        artifacts = [
            AnalysisArtifact(
                run_id=run.id,
                kind=ArtifactKind.SUMMARY,
                summary=analysis.summary.summary,
                evidence_ids=[doc.id for doc in extracted],
            ),
            AnalysisArtifact(
                run_id=run.id,
                kind=ArtifactKind.FINDINGS,
                summary=f"{len(analysis.findings)} findings",
                evidence_ids=[doc.id for doc in extracted],
            ),
            AnalysisArtifact(
                run_id=run.id,
                kind=ArtifactKind.THEMES,
                summary=f"{len(analysis.themes)} themes",
                evidence_ids=[doc.id for doc in extracted],
            ),
            AnalysisArtifact(
                run_id=run.id,
                kind=ArtifactKind.CONTRADICTIONS,
                summary=f"{len(analysis.contradictions)} contradictions",
                evidence_ids=[doc.id for doc in extracted],
            ),
        ]
        for artifact in artifacts:
            backend.save_analysis_artifact_metadata(artifact)

        report = ReporterAgent().build_report(run_id=run.id, objective=run.objective, analysis=analysis)

        artifact_dir, report_path = _save_analysis_artifacts(run.id, analysis)
        Path(report_path).write_text(report.markdown, encoding="utf-8")

        run = backend.update_run_status(run.id, RunStatus.COMPLETED)
        return RunResearchOutput(
            run=run,
            plan=plan,
            search_queries=queries,
            discovered_sources=discovered,
            fetched_documents=fetched,
            extracted_documents=extracted,
            analysis=analysis,
            analysis_artifacts=artifacts,
            report_markdown=report.markdown,
            artifact_dir=artifact_dir,
            report_path=report_path,
        )
    except Exception as exc:
        run = backend.update_run_status(run.id, RunStatus.FAILED, error_message=str(exc))
        raise
