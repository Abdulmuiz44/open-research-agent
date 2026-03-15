# Open Research Agent

## Status

**Production Packaging and Deployment Readiness Implemented**

Open Research Agent is a Python-first, CLI-first MVP for bounded local research runs using deterministic discovery/fetch/extract/analyze/report steps.

## MVP Scope Alignment

This repository remains aligned with `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/MVP_SCOPE.md`, and `docs/TASKLIST.md`:

- single-service, local-first runtime
- no frontend UI
- no distributed infrastructure
- no remote database dependency
- no Kubernetes/cloud deployment stack

## Development Run (Local)

1. Install Python 3.11+.
2. Install dependencies:
   - `uv sync --extra dev`
3. Optional `.env` overrides with `ORA_` prefix.

CLI commands:

- `uv run ora --help`
- `uv run ora health`
- `uv run ora research "Compare open-source HTML extraction libraries" --max-sources 6`

API command:

- `uv run uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload`

## Packaged / Containerized Run

### Docker build + run

- Build: `docker build -t open-research-agent:local .`
- Run:
  - `docker run --rm -p 8000:8000 --env-file .env -v "$(pwd)/outputs:/app/outputs" open-research-agent:local`

### Compose run

- `docker compose up --build`

The compose setup mounts local `./outputs` into container `/app/outputs`.

## Environment Variables

All configuration uses `ORA_` prefix.

Required in specific cases:

- `ORA_SEARCH_API_KEY` when `ORA_SEARCH_PROVIDER` is `serpapi` or `tavily`

Common optional settings:

- `ORA_ENVIRONMENT` (`development|test|staging|production`)
- `ORA_SERVICE_MODE` (`api|cli`)
- `ORA_LOG_LEVEL` (`DEBUG|INFO|WARNING|ERROR|CRITICAL`)
- `ORA_API_HOST` (IP, `localhost`, or hostname)
- `ORA_API_PORT` (1..65535)
- `ORA_DATA_DIR` (default `outputs`)
- `ORA_RUNS_DIR` (default `<ORA_DATA_DIR>/runs`)
- `ORA_ARTIFACTS_DIR` (default `<ORA_DATA_DIR>/artifacts`)
- `ORA_REPORTS_DIR` (default `<ORA_DATA_DIR>/reports`)
- `ORA_METADATA_DIR` (default `<ORA_DATA_DIR>/metadata`)
- `ORA_SEARCH_PROVIDER`
- `ORA_SEARCH_ENDPOINT`
- `ORA_REQUEST_TIMEOUT_SECONDS`
- `ORA_REQUEST_RETRIES`
- `ORA_USER_AGENT`
- `ORA_MAX_SOURCES_PER_RUN`
- `ORA_MAX_FETCH_PER_RUN`

Provider-related optional settings:

- `ORA_OPENAI_API_KEY`
- `ORA_ANTHROPIC_API_KEY`

## Health and Readiness

- `GET /health`: basic liveness for service process and config load.
- `GET /ready`: readiness for local startup dependencies (validated writable persistence paths and bootstrap completion).

## Persistence and Artifact Paths

At startup, runtime prepares and validates these paths:

- `<ORA_DATA_DIR>`
- `<ORA_DATA_DIR>/runs`
- `<ORA_DATA_DIR>/artifacts`
- `<ORA_DATA_DIR>/reports`
- `<ORA_DATA_DIR>/metadata`

Paths are created if missing and checked for writability.

## Current Deployment Limitations (Intentional)

- single-process local MVP deployment only
- in-memory storage backend is still used for run metadata
- no background workers or distributed job orchestration
- no managed observability stack

See `docs/DEPLOYMENT.md` for operational details and troubleshooting.
