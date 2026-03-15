from pathlib import Path

from src.data.models import ExtractedDocument, ResearchRun
from src.data.storage import LocalStorageStub


def test_storage_saves_extracted_and_lists_artifacts(tmp_path: Path) -> None:
    storage = LocalStorageStub(base_dir=tmp_path / "runs")
    run_id = "run-storage"
    storage.save_artifact_json(run_id, "manifest.json", {"run_id": run_id})

    doc = ExtractedDocument(
        run_id=run_id,
        source_id="s1",
        source_url="https://example.com",
        final_url="https://example.com",
        domain="example.com",
        title="x",
        raw_content="raw",
        content="clean",
    )
    storage.save_extracted_document(doc)

    artifacts = storage.list_run_artifacts(run_id)
    assert "manifest.json" in artifacts
    assert any(path.startswith("extracted/") for path in artifacts)
    assert storage.get_run_artifact_refs(run_id)


def test_storage_loads_run_and_artifacts_after_restart(tmp_path: Path) -> None:
    base_dir = tmp_path / "runs"
    storage = LocalStorageStub(base_dir=base_dir)
    run = storage.create_run(ResearchRun(objective="persisted objective"))
    storage.update_run_status(run.id, run.status)
    storage.save_artifact_json(
        run.id,
        "manifest.json",
        {
            "run_id": run.id,
            "objective": run.objective,
            "status": run.status.value,
            "created_at": run.created_at.isoformat(),
            "updated_at": run.updated_at.isoformat(),
            "paths": {"report": "report/report.md"},
        },
    )
    storage.save_artifact_markdown(run.id, "report/report.md", "# report")

    restarted = LocalStorageStub(base_dir=base_dir)

    loaded = restarted.get_run(run.id)
    assert loaded is not None
    assert loaded.id == run.id
    assert loaded.objective == "persisted objective"

    artifacts = restarted.list_run_artifacts(run.id)
    assert "manifest.json" in artifacts
    assert "report/report.md" in artifacts

    refs = restarted.get_run_artifact_refs(run.id)
    assert refs["report"].endswith("report/report.md")

    recent = restarted.list_runs(limit=1)
    assert len(recent) == 1
    assert recent[0].id == run.id
