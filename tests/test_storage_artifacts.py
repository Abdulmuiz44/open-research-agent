from pathlib import Path

from src.data.models import ExtractedDocument, ResearchRun
from src.data.storage import LocalStorageStub


def test_storage_saves_extracted_and_lists_artifacts(tmp_path: Path) -> None:
    storage = LocalStorageStub(base_dir=tmp_path / "runs")
    run = storage.create_run(ResearchRun(id="run-storage", objective="test"))
    storage.save_artifact_json(run.id, "manifest.json", {"run_id": run.id})

    doc = ExtractedDocument(
        run_id=run.id,
        source_id="s1",
        source_url="https://example.com",
        final_url="https://example.com",
        domain="example.com",
        title="x",
        raw_content="raw",
        content="clean",
    )
    storage.save_extracted_document(doc)

    artifacts = storage.list_run_artifacts(run.id)
    assert "manifest.json" in artifacts
    assert any(path.startswith("extracted/") for path in artifacts)
    assert storage.get_run_artifact_refs(run.id)
    assert storage.list_runs()[0].id == run.id
