# Open Research Agent

Open Research Agent is an open-source, Python-first system for bounded research workflows over web and local data sources.

## Current Status

**Deterministic Analysis Layer Implemented** — the project now runs a bounded local flow with real source discovery/fetch/extraction and deterministic multi-document analysis with inspectable findings, themes, evidence mappings, contradictions, and report artifacts.

## What is Implemented Now

- Deterministic plan-to-query generation.
- Real search provider abstraction with a local DuckDuckGo HTML provider.
- Source ranking and URL deduplication heuristics.
- Real HTTP fetch layer with timeout/retry/user-agent controls and fetch metadata capture.
- Bounded browser fetch placeholder interface (`browser_fetch_not_enabled`).
- Simple bounded extraction path (Trafilatura + HTML title fallback + cleaned body text).
- Deterministic analysis layer over extracted documents:
  - recurring-theme detection from repeated terms
  - structured findings with evidence mapping (source IDs, URLs, snippets, confidence)
  - conservative contradiction detection for obvious numeric disagreements
  - run-level analysis summary with bounded limitations
- Deterministic report generation using analysis outputs.
- Workflow artifact saving under `outputs/runs/<run_id>/analysis/`:
  - `findings.json`
  - `themes.json`
  - `contradictions.json`
  - `analysis_summary.json`
  - plus `outputs/runs/<run_id>/report.md`
- CLI/API run responses now include analysis counts and artifact/report references.

## What Remains Intentionally Deferred

- Full crawler orchestration and autonomous browsing.
- Playwright browser automation implementation.
- LLM-driven planning/ranking/analysis prose generation.
- Durable database-backed persistence.
- Vector search, embeddings, and advanced retrieval.
- Advanced extraction (PDF/OCR/site-specific strategies).
- Advanced NLP/ML analysis pipelines.

## Inspecting Analysis Outputs Locally

1. Run research: `uv run ora research "Your objective" --max-sources 6`
2. Capture `run_id` from CLI output.
3. Inspect artifacts:
   - `outputs/runs/<run_id>/analysis/findings.json`
   - `outputs/runs/<run_id>/analysis/themes.json`
   - `outputs/runs/<run_id>/analysis/contradictions.json`
   - `outputs/runs/<run_id>/analysis/analysis_summary.json`
   - `outputs/runs/<run_id>/report.md`

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

## Run Locally

- CLI health: `uv run ora health`
- CLI research flow:
  - `uv run ora research "Compare open-source HTML extraction libraries" --max-sources 6`
- API server:
  - `uv run uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload`
- API run execution:
  - `curl -X POST http://127.0.0.1:8000/runs -H 'content-type: application/json' -d '{"objective":"Compare open-source HTML extraction libraries","max_sources":6}'`
