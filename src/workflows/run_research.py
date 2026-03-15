"""Research workflow orchestration for bounded local runs."""

from __future__ import annotations

import asyncio
from pathlib import Path

from pydantic import BaseModel, Field

from src.analysis.report_builder import render_report_markdown
from src.core.config import get_settings
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
from src.workflows.artifact_manifest import ManifestBuilder, RunArtifactLayout


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
        manifest = ManifestBuilder(run_id=run.id, objective=run.objective, created_at=run.created_at)

        backend.save_artifact_json(
            run.id,
            RunArtifactLayout.MANIFEST,
            manifest.payload(status=run.status, updated_at=run.updated_at),
        )

        provider = build_search_provider(get_settings())
        crawler = Crawler(provider)
        discovered = crawler.discover(run.id, queries)
        fetched = asyncio.run(crawler.fetch(discovered))

        extractor = Extractor()
        extracted = [extractor.extract(doc) for doc in fetched if doc.success and (doc.raw_html or doc.text)]

        plan_path = backend.save_artifact_json(run.id, RunArtifactLayout.PLAN, plan.model_dump(mode="json"))
        manifest.add(artifact_id="plan", kind="plan", path=plan_path)

        sources_path = backend.save_artifact_json(
            run.id,
            RunArtifactLayout.SOURCES,
            [source.model_dump(mode="json") for source in discovered],
        )
        manifest.add(artifact_id="sources", kind="sources", path=sources_path)

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

        fetched_paths: list[str] = []
        for document in fetched:
            backend.save_fetched_document_metadata(document)
            fetched_path = backend.get_run_artifact_refs(run.id)[f"fetched_{document.source_id}"]
            fetched_paths.append(fetched_path)
            manifest.add(artifact_id=document.id, kind="fetched_metadata", path=fetched_path)

        for document in extracted:
            backend.save_extracted_document(document)
            extracted_file_path = backend.get_run_artifact_refs(run.id)[f"extracted_{document.source_id}"]
            manifest.add(artifact_id=document.id, kind="extracted_metadata", path=extracted_file_path)

        fetched_success = len([d for d in fetched if d.success])
        summary = f"Discovered {len(discovered)} sources, fetched {fetched_success}, extracted {len(extracted)} documents."
        artifact = AnalysisArtifact(
            run_id=run.id,
            kind=ArtifactKind.SUMMARY,
            summary=summary,
            evidence_ids=[doc.id for doc in extracted],
        )
        backend.save_analysis_artifact_metadata(artifact)
        analysis_path = backend.get_run_artifact_refs(run.id)[f"analysis_{artifact.id}"]
        manifest.add(artifact_id=artifact.id, kind=f"analysis_{artifact.kind.value}", path=analysis_path)

        report_markdown = render_report_markdown(
            run_id=run.id,
            objective=run.objective,
            summary=summary,
            sources=discovered,
            extracted_documents=extracted,
            findings=[summary],
            limitations=["Analysis is deterministic and lightweight in this MVP stage."],
        )
        report_path = backend.save_artifact_markdown(run.id, RunArtifactLayout.REPORT, report_markdown)
        manifest.add(artifact_id="report", kind="report", path=report_path)

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
        manifest.add(artifact_id="final_result", kind="analysis_result", path=final_result_path)

        manifest_path = backend.save_artifact_json(
            run.id,
            RunArtifactLayout.MANIFEST,
            manifest.payload(status=run.status, updated_at=run.updated_at),
        )
        manifest.add(artifact_id=RunArtifactLayout.MANIFEST, kind="manifest", path=manifest_path)
        manifest_path = backend.save_artifact_json(
            run.id,
            RunArtifactLayout.MANIFEST,
            manifest.payload(status=run.status, updated_at=run.updated_at),
        )

        artifact_refs = backend.get_run_artifact_refs(run.id)
        if fetched_paths:
            artifact_refs["fetched"] = fetched_paths[0]
        artifact_refs.update(
            {
                "plan": plan_path,
                "sources": sources_path,
                "report": report_path,
                "manifest": manifest_path,
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
            artifact_dir=str(Path(manifest_path).parent.resolve()),
            artifact_paths=backend.list_run_artifacts(run.id),
            artifact_refs=artifact_refs,
        )
    except Exception as exc:
        backend.update_run_status(run.id, RunStatus.FAILED, error_message=str(exc))
        raise
