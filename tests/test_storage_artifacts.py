from pathlib import Path

from src.data.models import (
    ArtifactKind,
    AnalysisArtifact,
    ExtractedDocument,
    FetchedDocument,
    ResearchPlan,
    ResearchRun,
    RunStatus,
    Source,
)
from src.data.storage import LocalStorageStub, SQLiteStorageBackend


def _exercise_backend(storage) -> None:
    run = storage.create_run(ResearchRun(id="run-storage", objective="storage objective"))
    storage.update_run_status(run.id, RunStatus.RUNNING)

    plan = ResearchPlan(objective=run.objective, research_objectives=["a"], search_queries=["q"], source_budget=3)
    plan_path = storage.save_plan_artifact(run.id, plan)
    assert plan_path.endswith("plan.json")

    source = Source(id="s1", run_id=run.id, url="https://example.com", domain="example.com", title="Example")
    saved_source = storage.save_source_metadata(source)
    assert saved_source.id == source.id

    fetched = FetchedDocument(
        id="f1",
        run_id=run.id,
        source_id=source.id,
        requested_url="https://example.com",
        final_url="https://example.com",
        status_code=200,
        success=True,
        text="hello",
    )
    storage.save_fetched_metadata(fetched)

    doc = ExtractedDocument(
        id="e1",
        run_id=run.id,
        source_id=source.id,
        source_url="https://example.com",
        final_url="https://example.com",
        domain="example.com",
        title="x",
        raw_content="raw",
        content="clean",
    )
    storage.save_extracted_document_metadata(doc)

    analysis = AnalysisArtifact(
        id="a1",
        run_id=run.id,
        kind=ArtifactKind.SUMMARY,
        summary="summary",
        evidence_ids=[doc.id],
    )
    storage.save_analysis_artifact_metadata(analysis)

    report_path = storage.save_artifact_markdown(run.id, "report/report.md", "# Report")
    storage.save_report_artifact_metadata(run.id, report_path)

    artifacts = storage.get_run_artifacts(run.id)
    assert "plan.json" in artifacts
    assert "report/report.md" in artifacts
    assert any(path.startswith("fetched/") for path in artifacts)

    sources = storage.get_run_sources(run.id)
    assert len(sources) == 1
    assert sources[0].id == source.id

    listed_runs = storage.list_runs(limit=10, offset=0)
    assert listed_runs
    assert listed_runs[0].id == run.id


def test_local_storage_backend_methods(tmp_path: Path) -> None:
    _exercise_backend(LocalStorageStub(base_dir=tmp_path / "runs"))


def test_sqlite_storage_backend_methods(tmp_path: Path) -> None:
    _exercise_backend(SQLiteStorageBackend(base_dir=tmp_path / "runs", db_path=tmp_path / "runs" / "storage.sqlite3"))
