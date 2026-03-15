from pathlib import Path

from src.data.models import ExtractedDocument
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


def test_storage_can_rehydrate_run_and_artifacts_from_disk(tmp_path: Path) -> None:
    run_id = "rehydrate-run"
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)
    report_path = run_dir / "report" / "report.md"
    report_path.parent.mkdir(parents=True)
    report_path.write_text("# report", encoding="utf-8")

    manifest_payload = {
        "run_id": run_id,
        "objective": "rehydrate objective",
        "status": "completed",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:01+00:00",
        "paths": {"report": str(report_path)},
    }
    (run_dir / "manifest.json").write_text(__import__("json").dumps(manifest_payload), encoding="utf-8")

    storage = LocalStorageStub(base_dir=tmp_path / "runs")
    run = storage.get_run(run_id)
    assert run is not None
    assert run.status.value == "completed"

    artifacts = storage.list_run_artifacts(run_id)
    assert "manifest.json" in artifacts
    assert "report/report.md" in artifacts

    refs = storage.get_run_artifact_refs(run_id)
    assert refs["report"] == str(report_path)
