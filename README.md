# Open Research Agent

Open Research Agent is a Python-first, CLI-first system for bounded research workflows over web sources with local artifact persistence.

## Status

**v0.1.0 MVP Hardened**

## What it does today

- Accepts a bounded objective and constraints.
- Generates deterministic research queries.
- Discovers sources using a provider abstraction.
- Fetches pages with HTTP-first behavior and bounded browser fallback decisioning.
- Extracts normalized content and metadata from fetched pages.
- Produces deterministic report artifacts and JSON run summaries.
- Persists run metadata and artifact references for inspection.
- Exposes CLI and API run retrieval and artifact inspection paths.

## Implemented MVP surface

### CLI

- `ora health`
- `ora research "<objective>" --max-sources 6`
- `ora get <run_id>`
- `ora list`
- `ora artifacts <run_id>`

### API

- `GET /health`
- `GET /ready`
- `POST /runs`
- `GET /runs`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/artifacts`

## Run data and artifacts

- Run metadata storage: in-memory run index + local run directories.
- Run artifact root: `outputs/runs/<run_id>/`
- Key artifacts:
  - `manifest.json`
  - `plan.json`
  - `sources.json`
  - `fetched/documents.json`
  - `extracted/documents.json`
  - `analysis/final_result.json`
  - `report/report.md`

## Health/readiness behavior

- `/health` reports service metadata.
- `/ready` verifies local runtime readiness with resolved run storage path.

## Local packaged run behavior

- Install: `uv sync --extra dev`
- CLI health: `uv run ora health`
- Run research: `uv run ora research "Compare open-source HTML extraction libraries" --max-sources 6`
- API: `uv run uvicorn apps.api.main:app --host 127.0.0.1 --port 8000`

## Deferred beyond v0.1.0

- Full crawler automation and autonomous browsing.
- Browser automation implementation details (placeholder fetch path only).
- LLM-generated prose reporting.
- Vector search, OCR, and PDF parsing.
- Distributed persistence/infrastructure.

## Current limitations

- Search results vary by remote provider behavior.
- Browser fetch execution is intentionally deferred.
- Extraction is intentionally lightweight and deterministic.
- Persistence is local MVP storage, not production-grade.

## Release baseline

See:

- `CHANGELOG.md`
- `docs/RELEASE_NOTES_V0_1.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/TESTING.md`
