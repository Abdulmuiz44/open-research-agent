# Open Research Agent

Open Research Agent is an open-source, Python-first system for bounded research workflows over web and local data sources.

## Current Status

**Foundation Implemented** — the runtime foundation is now runnable (config, logging, data contracts, CLI, and API), while research/search/extraction/analysis/report execution logic remains intentionally deferred.

## What is Implemented

- Environment-driven settings with `.env` support (`ORA_` prefix).
- Shared logging setup used by both CLI and API.
- Base exception hierarchy for config/validation/storage/workflow concerns.
- Concrete Pydantic data models for runs, sources, extracted documents/tables, and analysis artifacts.
- Storage interfaces plus a minimal local in-memory stub for runtime/testing.
- Runnable CLI with:
  - `ora health`
  - `ora research` (placeholder)
  - `ora fetch` (placeholder)
  - `ora analyze` (placeholder)
- Runnable FastAPI app with:
  - `GET /health`
  - `POST /runs` (metadata placeholder)
  - `GET /runs/{run_id}` (metadata placeholder)
- Tests for imports, config, CLI health/help, and API health/run creation.

## What is Intentionally Deferred

- Real planning workflow orchestration.
- Search provider execution.
- Web fetching/crawling/extraction.
- Analysis and report generation.
- Durable persistence/database implementation.
- External LLM provider calls.

## Local Setup

1. Install Python 3.11 and `uv`.
2. Install dependencies:
   - `uv sync --extra dev`
3. Optional: create `.env` file and set overrides:
   - `ORA_ENVIRONMENT=development`
   - `ORA_LOG_LEVEL=INFO`
   - `ORA_API_HOST=127.0.0.1`
   - `ORA_API_PORT=8000`

## Run Tests

- `uv run pytest`

## Run CLI

- Show help: `uv run ora --help`
- Health check: `uv run ora health`
- Placeholder commands:
  - `uv run ora research "Your objective"`
  - `uv run ora fetch "https://example.com"`
  - `uv run ora analyze "<run_id>"`

## Run API

- Start server:
  - `uv run uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload`
- Example checks:
  - `curl http://127.0.0.1:8000/health`
  - `curl -X POST http://127.0.0.1:8000/runs -H 'content-type: application/json' -d '{"objective":"test run"}'`
