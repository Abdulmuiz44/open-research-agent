# Open Research Agent

Open Research Agent is an open-source, Python-first system for bounded research workflows over web and local data sources.

## Current Status

**Real Search and Fetch Layer Started** — the project now runs a bounded local flow with real source discovery and real HTTP fetching, while extraction/analysis/reporting remain intentionally simple and deterministic.

## What is Implemented Now

- Deterministic plan-to-query generation.
- Real search provider abstraction with a local DuckDuckGo HTML provider.
- Source ranking and URL deduplication heuristics.
- Real HTTP fetch layer with timeout/retry/user-agent controls and fetch metadata capture.
- Bounded browser fetch placeholder interface (`browser_fetch_not_enabled`).
- Simple bounded extraction path (Trafilatura + HTML title fallback + cleaned body text).
- End-to-end workflow orchestration from objective → queries → discovery → fetch → extraction → simple summary/report.
- CLI `research` command executes the bounded real flow.
- API `POST /runs` executes the bounded real flow and returns run summary counts.
- Local in-memory run storage remains the default persistence for this phase.

## What Remains Intentionally Deferred

- Full crawler orchestration and autonomous browsing.
- Playwright browser automation implementation.
- LLM-driven planning/ranking/analysis.
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

## Known Limitations

- Search provider may vary by network availability and remote result changes.
- Browser fetch is a non-active placeholder in this step.
- Extraction quality is intentionally basic and bounded.
- Local in-memory storage resets when process exits.
