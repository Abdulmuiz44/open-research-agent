# Open Research Agent

Open Research Agent is a Python-first MVP for bounded research workflows over public web sources.

## v0.1 MVP Status

**Release candidate (v0.1.0)**

The MVP supports deterministic local runs that persist inspectable artifacts for each stage:

1. plan/query generation
2. source discovery
3. HTTP fetch
4. bounded extraction
5. deterministic analysis summary
6. report generation

## Implemented Surface (v0.1)

- CLI commands:
  - `ora health`
  - `ora research "<objective>" --max-sources <n>`
  - `ora fetch <url>` (intentionally limited)
  - `ora analyze <run_id>` (intentionally limited)
- API endpoints:
  - `GET /health`
  - `GET /ready`
  - `POST /runs`
  - `GET /runs/{run_id}`
  - `GET /runs/{run_id}/artifacts`
- Local run storage and artifact persistence under `outputs/runs/<run_id>/`.
- Deterministic report and final result output.
- Browser fetch fallback placeholder (`browser_fetch_not_enabled`) for bounded non-MVP behavior.

## Artifact and Output Paths

Each run writes artifacts under `outputs/runs/<run_id>/`, including:

- `manifest.json`
- `plan.json`
- `sources.json`
- `fetched/documents.json`
- `extracted/documents.json`
- `analysis/final_result.json`
- `report/report.md`

`analysis/final_result.json` includes release-critical run metadata and counts:

- `run_id`, `status`, `query`/`objective`
- `created_at`, `updated_at`
- source/fetch/extraction counts
- findings/themes counts
- `artifact_dir`, `artifact_count`, `report_path`

## Quickstart

1. Install Python 3.11+ and `uv`
2. Install deps:
   - `uv sync --extra dev`
3. Optional env setup:
   - `cp .env.example .env`

Run CLI:

- `uv run ora health`
- `uv run ora research "Compare open-source HTML extraction libraries" --max-sources 6`

Run API:

- `uv run uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload`
- `curl -X POST http://127.0.0.1:8000/runs -H 'content-type: application/json' -d '{"objective":"Compare open-source HTML extraction libraries","max_sources":6}'`

Inspect a run:

- `curl http://127.0.0.1:8000/runs/<run_id>`
- `curl http://127.0.0.1:8000/runs/<run_id>/artifacts`

## Deferred (Out of v0.1 Scope)

- Full browser automation for fetch fallback
- OCR/PDF parsing pipelines
- Vector search and advanced retrieval stacks
- Distributed infrastructure and production-grade multi-node persistence
- Autonomous open-ended agent loops
