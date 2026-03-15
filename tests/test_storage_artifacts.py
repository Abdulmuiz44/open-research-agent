from pathlib import Path

from src.data.models import ExtractedDocument, FetchedDocument, ResearchRun, RunStatus, Source
from src.data.storage import SQLiteStorageBackend


def test_storage_saves_extracted_and_lists_artifacts(tmp_path: Path) -> None:
    db_path = tmp_path / "outputs" / "metadata.sqlite3"
    storage = SQLiteStorageBackend(base_dir=tmp_path / "outputs" / "runs", db_path=db_path)
    run = storage.create_run(ResearchRun(id="run-storage", objective="storage objective"))

    storage.save_artifact_json(run.id, "manifest.json", {"run_id": run.id})
    storage.save_source(
        Source(
            id="source-1",
            run_id=run.id,
            url="https://example.com",
            domain="example.com",
            title="Example",
        )
    )

    fetched = FetchedDocument(
        run_id=run.id,
        source_id="source-1",
        requested_url="https://example.com",
        final_url="https://example.com",
        status_code=200,
        success=True,
    )
    storage.save_fetched_document_metadata(fetched)

    doc = ExtractedDocument(
        run_id=run.id,
        source_id="source-1",
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
    refs = storage.get_run_artifact_refs(run.id)
    assert refs
    assert "manifest.json" in refs


def test_storage_updates_run_status(tmp_path: Path) -> None:
    storage = SQLiteStorageBackend(base_dir=tmp_path / "runs", db_path=tmp_path / "metadata.sqlite3")
    run = storage.create_run(ResearchRun(id="run-status", objective="status objective"))

    updated = storage.update_run_status(run.id, RunStatus.RUNNING)
    assert updated.status == RunStatus.RUNNING

    failed = storage.update_run_status(run.id, RunStatus.FAILED, error_message="boom")
    assert failed.status == RunStatus.FAILED
    assert failed.error_message == "boom"
