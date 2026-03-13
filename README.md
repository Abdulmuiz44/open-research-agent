# Open Research Agent

Open Research Agent is an open-source, Python-first system for bounded research workflows over web and local data sources.

## Current Status

**Scaffolded** — repository structure, typed interfaces, and entrypoints are in place; core business logic remains intentionally unimplemented.

## Stack Summary

- Python 3.11+
- CLI: Typer + Rich
- API: FastAPI + Uvicorn
- Models/validation: Pydantic + PydanticAI
- LLM routing: LiteLLM
- Web acquisition: HTTPX + Playwright + Crawl4AI
- Extraction: Trafilatura + Selectolax
- Data/analysis: Polars + pandas + DuckDB + PyArrow
- Tooling: uv + Ruff + Pytest

## Repository Structure

```text
apps/
  api/
  cli/
src/
  core/
  agents/
  search/
  web/
  data/
  analysis/
  llm/
  workflows/
tests/
docs/
outputs/
```

## Setup (Scaffold Phase)

1. Install Python 3.11 and `uv`.
2. Create environment and install dependencies:
   - `uv sync --extra dev`
3. Copy and configure environment variables:
   - `cp .env.example .env`
4. Run smoke tests:
   - `uv run pytest`

## Next Implementation Milestone

Implement request intake, planner, and search provider path to produce bounded candidate sources with provenance, aligned to `docs/TASKLIST.md` Phase 3–4.
