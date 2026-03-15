# Open Research Agent v0.1 Release Notes

## What v0.1 Supports

- Bounded research runs via CLI/API.
- Deterministic plan/query generation and source discovery.
- HTTP fetching with bounded limits and metadata capture.
- Deterministic extraction into structured artifacts.
- Deterministic final report generation and persisted run artifacts.
- Run retrieval and artifact listing from local storage.

## Deferred for Post-v0.1

- Full browser automation fallback execution.
- OCR/PDF parsing.
- Vector search and advanced retrieval.
- Distributed/production-scale infrastructure.

## How to Run

- CLI:
  - `uv run ora health`
  - `uv run ora research "<objective>" --max-sources 6`
- API:
  - `uv run uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload`
  - `POST /runs`, `GET /runs/{run_id}`, `GET /runs/{run_id}/artifacts`

## Known Limitations

- Search result quality/ordering depends on upstream provider behavior.
- Browser fallback currently returns `browser_fetch_not_enabled` placeholder output.
- Storage is local file-backed MVP persistence.
