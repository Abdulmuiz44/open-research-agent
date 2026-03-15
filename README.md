# Open Research Agent

Open Research Agent is an open-source, Python-first system for bounded research workflows over web and local data sources.

## Current Status

**Bounded Browser Fallback and Extraction Robustness Implemented** — the pipeline now runs HTTP-first fetch with selective single-page browser fallback, improved deterministic extraction on noisy/dynamic pages, and persisted fallback/extraction metadata artifacts.

## What is Implemented Now

- Deterministic plan-to-query generation.
- Real search provider abstraction with a local DuckDuckGo HTML provider.
- Source ranking and URL deduplication heuristics.
- Real HTTP fetch layer with timeout/retry/user-agent controls and fetch metadata capture.
- **Bounded browser fallback path** for recovery when HTTP output is blocked, near-empty, or JS-heavy.
- **Single-page browser render behavior** with strict timeout/wait bounds and no autonomous navigation.
- Improved extraction robustness:
  - stronger title extraction (`og:title`, `<title>`, then `<h1>`)
  - metadata enrichment (canonical URL, description, author, published time)
  - boilerplate line filtering and bounded deterministic content cleanup
  - extraction quality/text-length indicators
- Artifact writing per run for fetch metadata, extraction summaries, and generated report.
- End-to-end workflow orchestration from objective → queries → discovery → fetch/fallback → extraction → simple summary/report.
- CLI `research` command now reports HTTP/browser/fallback counts and artifact paths.
- API `POST /runs` now returns bounded fallback and extraction summary metadata.
- Local in-memory run storage persists run metadata and artifact path references for this phase.

## What Remains Intentionally Deferred

- Full crawler orchestration and autonomous browsing.
- Multi-page browser automation and interaction loops (click/scroll/session automation).
- Login/session handling.
- LLM-driven planning/ranking/analysis changes in this step.
- Durable database-backed persistence.
- Vector search and advanced retrieval.
- Advanced extraction outside scope (PDF parsing, OCR, site-specific heavy strategies).

## Browser Fallback Trigger Rules

Browser fallback is optional and bounded. It is triggered only when enabled and HTTP results are clearly weak:

- blocked-like HTTP statuses (`401`, `403`, `429`, `503`)
- empty HTML
- near-empty extracted visible text
- JS-heavy markers combined with weak visible text

HTTP remains the preferred primary path.

## Environment Variables

All runtime config uses `ORA_` prefix:

- `ORA_SEARCH_PROVIDER` (default: `duckduckgo_html`)
- `ORA_SEARCH_ENDPOINT` (default: `https://duckduckgo.com/html/`)
- `ORA_REQUEST_TIMEOUT_SECONDS` (default: `10.0`)
- `ORA_REQUEST_RETRIES` (default: `2`)
- `ORA_USER_AGENT` (default: `open-research-agent/0.1 (+https://example.local)`)
- `ORA_MAX_SOURCES_PER_RUN` (default: `8`)
- `ORA_MAX_FETCH_PER_RUN` (default: `6`)
- `ORA_BROWSER_FALLBACK_ENABLED` (default: `true`)
- `ORA_BROWSER_FALLBACK_MIN_TEXT_CHARS` (default: `200`)
- `ORA_BROWSER_FALLBACK_TIMEOUT_SECONDS` (default: `8.0`)
- `ORA_BROWSER_FALLBACK_WAIT_SECONDS` (default: `1.5`)

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
