# Open Research Agent

Open Research Agent is an open-source, Python-first system for bounded research workflows over web and local data sources.

## Current Status

**Real Extraction and Local Artifacts Implemented** — the project now runs a bounded local flow with real source discovery, real HTTP fetching, deterministic extraction into structured evidence, and per-run inspectable artifacts on disk.

## What is Implemented Now

- Deterministic plan-to-query generation.
- Real search provider abstraction with a local DuckDuckGo HTML provider.
- Source ranking and URL deduplication heuristics.
- Real HTTP fetch layer with timeout/retry/user-agent controls and fetch metadata capture.
- Bounded browser fetch placeholder interface (`browser_fetch_not_enabled`).
- Real bounded extraction path with title, cleaned text, canonical URL, metadata extraction, whitespace normalization, and basic boilerplate filtering.
- Local artifact persistence per run under `outputs/runs/<run_id>/`.
- End-to-end workflow orchestration from objective → queries → discovery → fetch → extraction → deterministic report.
- CLI `research` output includes run and artifact details.
- API run endpoints include extracted-document and artifact metadata.

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
- LLM-driven planning/ranking/analysis/report prose.
- Durable database-backed persistence.
- Vector search and advanced retrieval.
- Advanced extraction (PDF/OCR/site-specific strategies).

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

## Known Limitations

- Search provider may vary by network availability and remote result changes.
- Browser fetch is a non-active placeholder in this step.
- Extraction quality is intentionally basic and bounded.
- Storage is local file-based and not a production database.
