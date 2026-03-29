"""Pipeline orchestration for end-to-end local research runs."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from src.core.exceptions import WorkflowError
from src.data.models import (
    AnalysisArtifact,
    ExtractedDocument,
    Report,
    ResearchPlan,
    ResearchRequest,
    ResearchRun,
    Source,
)
from src.data.storage import LocalStorage


class RunResearchInput(BaseModel):
    objective: str = Field(min_length=3)
    constraints: list[str] = Field(default_factory=list)
    max_sources: int = Field(default=5, ge=1, le=100)


class RunResearchOutput(BaseModel):
    run: ResearchRun
    plan: ResearchPlan
    report: Report
    report_markdown: str
    artifact_dir: str
    artifact_paths: list[str]
    artifact_refs: dict[str, str]


class ResearchWorkflow:
    """Coordinates bounded research stages from request to report."""

    def __init__(self, storage: LocalStorage | None = None) -> None:
        self.storage = storage or LocalStorage()

    def run(self, request: ResearchRequest) -> RunResearchOutput:
        run = ResearchRun(objective=request.objective, status="running")
        self.storage.create_run(run)

        try:
            plan = ResearchPlan(
                run_id=run.id,
                search_queries=[request.objective],
                source_budget=max(1, min(10, len(request.constraints) + 3)),
                stop_conditions=["max_sources_reached", "relevance_below_threshold"],
            )
            plan_path = self.storage.save_artifact_json(run.id, "plan.json", plan.model_dump(mode="json"))

            source = Source(run_id=run.id, url="https://example.com", title="Example Source")
            self.storage.save_source(source)

            document = ExtractedDocument(
                run_id=run.id,
                source_id=source.id,
                title="Example Source",
                content=f"Deterministic extracted content for objective: {request.objective}",
                extracted_at=datetime.now(UTC),
            )
            self.storage.save_document(document)

            analysis = AnalysisArtifact(
                run_id=run.id,
                kind="summary",
                summary=f"Generated one deterministic finding for objective '{request.objective}'.",
                evidence_ids=[document.id],
            )
            self.storage.save_analysis(analysis)

            report = Report(
                run_id=run.id,
                objective=request.objective,
                findings=[analysis.summary],
                limitations=["This is a deterministic MVP scaffold run with synthetic source content."],
            )
            markdown = self._render_markdown(report)
            report_path = self.storage.save_report(report, markdown)

            final_result = {
                "run_id": run.id,
                "status": "completed",
                "objective": run.objective,
                "source_count": 1,
                "extracted_count": 1,
                "findings_count": len(report.findings),
                "report_path": report_path,
            }
            final_result_path = self.storage.save_artifact_json(run.id, "analysis/final_result.json", final_result)

            run.status = "completed"
            self.storage.update_run(run)

            refs = self.storage.get_run_artifact_refs(run.id)
            refs.update(
                {
                    "plan": plan_path,
                    "report": report_path,
                    "final_result": final_result_path,
                }
            )
            self.storage.save_artifact_json(run.id, ".artifact_refs.json", refs)

            artifact_dir = str((Path(self.storage.runs_dir) / run.id).resolve())
            return RunResearchOutput(
                run=run,
                plan=plan,
                report=report,
                report_markdown=markdown,
                artifact_dir=artifact_dir,
                artifact_paths=self.storage.list_run_artifacts(run.id),
                artifact_refs=self.storage.get_run_artifact_refs(run.id),
            )
        except Exception as exc:  # pragma: no cover - boundary for workflow failures
            run.status = "failed"
            self.storage.update_run(run)
            raise WorkflowError(f"Run {run.id} failed: {exc}") from exc

    @staticmethod
    def _render_markdown(report: Report) -> str:
        findings = "\n".join(f"- {item}" for item in report.findings) or "- No findings"
        limitations = "\n".join(f"- {item}" for item in report.limitations) or "- No limitations"
        return "\n".join(
            [
                "# Research Report",
                "",
                f"Run ID: {report.run_id}",
                f"Objective: {report.objective}",
                "",
                "## Findings",
                findings,
                "",
                "## Limitations",
                limitations,
            ]
        )


def run_research_workflow(payload: RunResearchInput, storage: LocalStorage | None = None) -> RunResearchOutput:
    request = ResearchRequest(objective=payload.objective, constraints=payload.constraints)
    return ResearchWorkflow(storage=storage).run(request)
