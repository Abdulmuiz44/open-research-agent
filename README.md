# Open Research Agent

Open Research Agent is an open-source, Python-first system for bounded research workflows over web and local data sources.

## Current Status

**Report Generation and Local Persistence Implemented** — the project now runs a bounded local flow with deterministic report generation, local metadata persistence, and per-run inspectable artifacts on disk.

## What is Implemented Now

- Deterministic plan-to-query generation.
- Real search provider abstraction with a local DuckDuckGo HTML provider.
- Source ranking and URL deduplication heuristics.
- Real HTTP fetch layer with timeout/retry/user-agent controls and fetch metadata capture.
- Bounded browser fetch placeholder interface (`browser_fetch_not_enabled`).
- Real bounded extraction path with title, cleaned text, canonical URL, metadata extraction, whitespace normalization, and basic boilerplate filtering.
- Deterministic report generation (`report/report.md` plus `analysis/final_result.json`) from bounded extracted evidence.
- Local metadata persistence for run lifecycle and artifact references.
- Local artifact persistence per run under `outputs/runs/<run_id>/`.
- End-to-end workflow orchestration from objective → queries → discovery → fetch → extraction → deterministic report.
- CLI `research` output includes run and artifact details.
- API run endpoints include extracted-document and artifact metadata.

## Persistence Locations

- Run metadata SQLite file: `data/app.db`
- Run artifacts root: `outputs/runs/<run_id>/`
- Deterministic report artifacts:
  - `outputs/runs/<run_id>/analysis/final_result.json`
  - `outputs/runs/<run_id>/report/report.md`

## Run Artifacts

Each run writes inspectable files to:

- `outputs/runs/<run_id>/manifest.json`
- `outputs/runs/<run_id>/plan.json`
- `outputs/runs/<run_id>/sources.json`
- `outputs/runs/<run_id>/fetched/documents.json`
- `outputs/runs/<run_id>/extracted/documents.json`
- `outputs/runs/<run_id>/analysis/final_result.json`
- `outputs/runs/<run_id>/report/report.md`
- Additional per-document extracted artifacts under `outputs/runs/<run_id>/extracted/`

## What Remains Intentionally Deferred

- Full crawler orchestration and autonomous browsing.
- Playwright browser automation implementation.
- LLM prose generation for report writing (MVP reports are deterministic/templated).
- Vector search and advanced retrieval.
- OCR and PDF parsing pipelines.
- Distributed persistence/backing stores (single-node local persistence only in MVP).

## Environment Variables

All runtime config uses `ORA_` prefix:

- `ORA_SEARCH_PROVIDER` (default: `duckduckgo_html`)
- `ORA_SEARCH_ENDPOINT` (default: `https://duckduckgo.com/html/`)
- `ORA_REQUEST_TIMEOUT_SECONDS` (default: `10.0`)
- `ORA_REQUEST_RETRIES` (default: `2`)
- `ORA_USER_AGENT` (default: `open-research-agent/0.1 (+https://example.local)`)
- `ORA_MAX_SOURCES_PER_RUN` (default: `8`)
- `ORA_MAX_FETCH_PER_RUN` (default: `6`)

## Local Setup

1. Install Python 3.11 and `uv`.
2. Install dependencies:
   - `uv sync --extra dev`
3. Optional `.env` overrides (example):
   - `ORA_ENVIRONMENT=development`
   - `ORA_LOG_LEVEL=INFO`
   - `ORA_SEARCH_PROVIDER=duckduckgo_html`

## Run Locally

- CLI health: `uv run ora health`
- CLI research flow:
  - `uv run ora research "Compare open-source HTML extraction libraries" --max-sources 6`
- API server:
  - `uv run uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload`
- API run execution:
  - `curl -X POST http://127.0.0.1:8000/runs -H 'content-type: application/json' -d '{"objective":"Compare open-source HTML extraction libraries","max_sources":6}'`

## Inspect Outputs Locally

- Check the run directory printed by CLI/API.
- Open `manifest.json` for the artifact index.
- Review `extracted/documents.json` for structured extracted evidence.
- Read `report/report.md` for the deterministic run summary.

## Inspect Previous Runs (CLI/API)

- CLI:
  - Run and capture `run_id` from output:
    - `uv run ora research "Compare open-source HTML extraction libraries" --max-sources 6`
  - Inspect persisted artifacts for that run:
    - `cat outputs/runs/<run_id>/manifest.json`
    - `cat outputs/runs/<run_id>/report/report.md`
- API:
  - Fetch run metadata:
    - `curl http://127.0.0.1:8000/runs/<run_id>`
  - List artifact paths and references:
    - `curl http://127.0.0.1:8000/runs/<run_id>/artifacts`

## Known Limitations

- Search provider may vary by network availability and remote result changes.
- Browser fetch is a non-active placeholder in this step.
- Extraction quality is intentionally basic and bounded.
- Storage is local file-based and not a production database.
