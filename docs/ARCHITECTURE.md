# Architecture

## System Overview

Open Research Agent should be built as a single-process Python application with:

- a shared pipeline core
- a CLI as the primary V1 interface
- an API layer designed but deferred to later implementation

The architecture should match the product boundary in the PRD: a bounded research pipeline with agentic planning and decision-making inside explicit stage contracts.

Core execution path:

1. request intake
2. planning
3. search
4. fetch
5. extract
6. normalize
7. analyze
8. report
9. persist artifacts

## Core Pipeline Definition

The pipeline should be implemented as a sequence of application services operating over typed inputs and outputs:

```text
ResearchRequest
  -> RequestService
  -> PlanningService
  -> SearchService
  -> FetchService
  -> ExtractService
  -> NormalizeService
  -> AnalyzeService
  -> ReportService
  -> RunStorage
```

Rules for the pipeline:

- each stage receives a typed input model and returns a typed output model
- each stage writes its stage artifact before control moves to the next stage
- each stage emits explicit success or failure status
- later stages must read normalized artifacts rather than re-reading raw stage files directly
- the pipeline runner owns orchestration; stage modules do not call each other directly

## Architectural Decisions

- `CLI-first`: V1 should optimize for local use and contributor velocity, not service operations.
- `Typed artifacts`: every stage reads and writes well-defined Pydantic models.
- `Artifact persistence`: raw and normalized artifacts are stored for replay, debugging, and evaluation.
- `Deterministic where possible`: use code for transforms and rules; use models for planning and synthesis where they add clear value.
- `Provider abstraction`: external dependencies such as search and LLM access should be hidden behind interfaces.

## Concrete Folder Structure

Suggested repository layout for V1:

```text
open-research-agent/
  docs/
    PRD.md
    ARCHITECTURE.md
    MVP_SCOPE.md
    TASKLIST.md
  src/
    open_research_agent/
      __init__.py
      config.py
      logging.py
      errors.py
      cli/
        app.py
        commands/
          run.py
          plan.py
          inspect.py
          report.py
          runs.py
      core/
        models/
          request.py
          plan.py
          source.py
          fetch.py
          extract.py
          evidence.py
          finding.py
          report.py
          run.py
        services/
          planner.py
          search.py
          fetcher.py
          extractor.py
          normalizer.py
          analyzer.py
          reporter.py
          pipeline.py
      providers/
        llm/
          base.py
          litellm_provider.py
        search/
          base.py
          <provider_name>.py
        extraction/
          trafilatura_extractor.py
          selectolax_fallback.py
        browser/
          playwright_fetcher.py
      storage/
        db.py
        repositories/
          runs.py
          sources.py
          evidence.py
          findings.py
        artifacts.py
      api/
        app.py
        routes/
          runs.py
          plan.py
      evaluation/
        datasets.py
        checks.py
      utils/
        urls.py
        hashes.py
        dates.py
        text.py
  tests/
    unit/
    integration/
    fixtures/
      pages/
      files/
      expected/
  data/
    app.db
    runs/
  scripts/
  pyproject.toml
  README.md
```

## Module Breakdown

## 1. Request Layer

Purpose:

- validate user input
- resolve local file references
- create the initial `RunContext`

Inputs:

- objective
- constraints
- local file inputs
- output preferences

Outputs:

- `ResearchRequest`
- `RunContext`

## 2. Planner

Purpose:

- turn the request into a bounded execution plan
- decide what to search for and what evidence is needed
- set budgets and stop conditions

Outputs:

- `ResearchPlan`
- sub-questions
- search queries
- source budget
- stop conditions

V1 constraints:

- no recursive replanning loops
- no tool creation
- no unbounded browsing

## 3. Search

Purpose:

- execute search queries
- rank and deduplicate candidate URLs
- preserve query provenance

Outputs:

- `SearchResult`
- `CandidateSource`

Requirements:

- provider interface from day one
- normalized URL handling
- per-result metadata including rank and matched query

## 4. Fetch

Purpose:

- retrieve page content and response metadata
- choose between standard HTTP and browser rendering

Outputs:

- `FetchedDocument`
- raw HTML artifact
- fetch status and error details

Requirements:

- HTTP-first strategy with browser fallback
- request timeout and retry policy
- explicit handling for redirects and blocked fetches

## 5. Extract

Purpose:

- convert raw page content into readable structured text
- extract metadata needed for evidence and citation

Outputs:

- `ExtractedDocument`
- extracted text blocks
- extraction metadata

Requirements:

- preserve raw and cleaned forms
- avoid site-specific extraction rules in V1 unless they are necessary for evaluation fixtures

## 6. Normalize

Purpose:

- convert heterogeneous inputs into consistent records used by analysis and reporting

Outputs:

- `SourceRecord`
- `DocumentRecord`
- `EvidenceRecord`
- normalized tabular datasets

Requirements:

- stable IDs
- provenance fields for every evidence record
- normalized publication metadata where available

## 7. Analyze

Purpose:

- produce findings grounded in evidence
- support simple analysis across both text and tabular inputs

Outputs:

- `Finding`
- derived tables
- contradiction or gap markers

V1 boundaries:

- support comparison, synthesis, and lightweight aggregation
- do not attempt autonomous follow-up research loops after analysis

## 8. Report

Purpose:

- assemble final outputs for humans and programs

Outputs:

- Markdown report
- JSON result

Requirements:

- deterministic section layout
- evidence references for major findings
- explicit limitations and open questions

## 9. Storage

Purpose:

- persist all stage artifacts for replay and inspection

Requirements:

- every stored record is linked to `run_id`
- raw artifacts and normalized artifacts are both retained
- partial failures are queryable after a run

## Proposed Data Models

The final field list may change during implementation, but these models should exist before coding begins.

### `ResearchRequest`

- `run_id: str`
- `objective: str`
- `sub_questions: list[str] = []`
- `domains_allow: list[str] = []`
- `domains_deny: list[str] = []`
- `max_sources: int | None`
- `recency_days: int | None`
- `input_files: list[str] = []`
- `output_formats: list[str]`
- `created_at: datetime`

### `ResearchPlan`

- `run_id: str`
- `objective: str`
- `sub_questions: list[str]`
- `queries: list[PlanQuery]`
- `expected_evidence_types: list[str]`
- `source_budget: int`
- `stop_conditions: StopConditions`
- `notes: list[str]`

### `CandidateSource`

- `source_id: str`
- `run_id: str`
- `query_id: str`
- `url: str`
- `normalized_url: str`
- `domain: str`
- `title: str | None`
- `snippet: str | None`
- `rank: int`
- `selection_reason: str | None`

### `FetchedDocument`

- `fetch_id: str`
- `source_id: str`
- `run_id: str`
- `url: str`
- `final_url: str | None`
- `status_code: int | None`
- `fetch_method: str`
- `success: bool`
- `error_code: str | None`
- `content_type: str | None`
- `fetched_at: datetime`
- `artifact_path: str`

### `ExtractedDocument`

- `document_id: str`
- `source_id: str`
- `run_id: str`
- `title: str | None`
- `author: str | None`
- `published_at: datetime | None`
- `language: str | None`
- `text: str`
- `content_blocks: list[ContentBlock]`
- `content_hash: str`
- `extraction_method: str`

### `EvidenceRecord`

- `evidence_id: str`
- `run_id: str`
- `source_id: str`
- `document_id: str | None`
- `kind: str`
- `claim_text: str`
- `support_text: str`
- `citation_label: str`
- `provenance: EvidenceProvenance`

### `Finding`

- `finding_id: str`
- `run_id: str`
- `statement: str`
- `summary: str`
- `evidence_ids: list[str]`
- `confidence: str`
- `finding_type: str`

### `Report`

- `run_id: str`
- `objective: str`
- `method_summary: str`
- `findings: list[FindingSection]`
- `limitations: list[str]`
- `open_questions: list[str]`
- `sources_used: list[str]`
- `generated_at: datetime`

## Recommended Stack

### Runtime and Modeling

- Python 3.12+
- `uv`
- `Pydantic`
- `PydanticAI`
- `LiteLLM`

### Interfaces

- `Typer`
- `Rich`
- `FastAPI` later, reusing the same core services

### Web Acquisition and Extraction

- `HTTPX`
- `Playwright`
- `Trafilatura`
- `Selectolax`
- `Crawl4AI` only if it materially simplifies fetch or crawl behavior during implementation

### Data and Storage

- `SQLite`
- `DuckDB`
- `Polars`
- `pandas`
- `Parquet`

### Tooling

- `Ruff`
- `Pytest`

## Suggested Environment Variables

V1 should keep environment configuration small and explicit:

- `OPENAI_API_KEY`
- `LITELLM_MODEL`
- `ORA_DATA_DIR`
- `ORA_LOG_LEVEL`
- `ORA_MAX_SOURCES_DEFAULT`
- `ORA_HTTP_TIMEOUT_SECONDS`
- `ORA_FETCH_RETRIES`
- `ORA_ENABLE_BROWSER_FALLBACK`
- `ORA_USER_AGENT`
- `SEARCH_API_KEY`
- `PLAYWRIGHT_BROWSERS_PATH`

Configuration rules:

- every environment variable must have a documented default or explicit required status
- CLI flags should override environment settings for a single run
- the resolved config should be written into run metadata for reproducibility

## Data Flow

```text
ResearchRequest
  -> ResearchPlan
  -> SearchResult[]
  -> FetchedDocument[]
  -> ExtractedDocument[]
  -> EvidenceRecord[]
  -> Finding[]
  -> Report
```

Stage-by-stage flow:

1. `ResearchRequest` is validated and stored.
2. Planner produces `ResearchPlan` with budgets and stop conditions.
3. Search produces `CandidateSource` records linked to plan queries.
4. Fetch produces raw artifacts plus machine-readable fetch metadata.
5. Extract produces cleaned text and extraction metadata.
6. Normalize produces source, document, and evidence records with stable IDs.
7. Analyze produces findings and derived analytical artifacts.
8. Report produces Markdown and JSON outputs referencing evidence IDs.

## Storage Approach

V1 should use hybrid local storage:

- `SQLite` for run metadata, indexes, and queryable status
- filesystem for raw HTML, extracted text, and generated reports
- `Parquet` for larger normalized tables and analysis outputs

Suggested layout:

```text
data/
  app.db
  runs/
    <run_id>/
      request.json
      plan.json
      search_results.json
      fetch/
        <source_id>.html
        <source_id>.json
      extract/
        <source_id>.json
      normalize/
        evidence.parquet
        sources.parquet
      analyze/
        findings.json
        derived_tables.parquet
      report.md
      report.json
```

Recommended relational tables:

- `runs`
- `plans`
- `queries`
- `candidate_sources`
- `fetch_attempts`
- `documents`
- `evidence`
- `findings`
- `artifacts`

## API and CLI Direction

## CLI Direction

CLI is the required V1 interface.

Suggested commands:

- `ora run --objective "Compare top open-source web crawlers for research workflows" --max-sources 12 --output markdown,json`
- `ora run --objective "Summarize recent browser automation frameworks" --allow-domain github.com --allow-domain playwright.dev`
- `ora plan --objective "Analyze pricing claims in public AI tooling sites"`
- `ora inspect --run-id <run_id> --artifact evidence`
- `ora report --run-id <run_id> --format markdown`
- `ora runs`

Design rules:

- commands call shared application services, not separate logic paths
- stage progress and failures are visible in terminal output
- users can inspect a stored run without rerunning it

## API Direction

API is a design requirement for later phases, not a V1 implementation requirement.

V1 should still prepare for an API by:

- keeping request and result schemas transport-safe
- isolating CLI formatting from domain services
- avoiding direct terminal concerns inside the core pipeline

Likely later endpoints:

- `POST /runs` with `ResearchRequest` payload
- `GET /runs/{run_id}` for run status and summary stats
- `GET /runs/{run_id}/report?format=markdown|json`
- `GET /runs/{run_id}/artifacts`
- `GET /runs/{run_id}/evidence`
- `POST /plan` for plan-only generation

## Observability and Evaluation

V1 needs lightweight observability from the start:

- stage-level timings
- per-stage success and failure counts
- source counts, fetch counts, extraction counts
- citation coverage in final reports

The architecture should support an evaluation harness that runs fixed prompts and fixtures through the pipeline and records:

- extraction success rate
- evidence coverage
- report grounding checks

## Major Engineering Risks

- search provider changes or quotas may stall development if the abstraction is not implemented early
- browser fallback can create setup friction and slow runs if it becomes the default path
- extraction quality may vary sharply across page types, especially docs pages versus news/article pages
- evidence schemas may become unstable if raw extraction output is used directly in later stages
- report synthesis may drift from evidence unless citation enforcement is built into the finding model
- storage churn will slow delivery if file layout and run lifecycle are not frozen early

## Testing Strategy for V1

Testing should map directly to the launch criteria.

### Unit Tests

- schema validation for all core models
- URL normalization and hashing helpers
- planning output shape and stop-condition rules
- evidence-to-finding citation requirements

### Integration Tests

- request -> plan -> search on mocked provider responses
- fetch -> extract on fixture pages
- normalize -> analyze on mixed web and CSV or JSON inputs
- full pipeline run on a small deterministic fixture set

### Fixture Sets

- at least 5 static HTML fixtures
- at least 1 rendered-page fixture
- at least 2 local structured input fixtures
- expected outputs for citations, evidence counts, and required report sections

### Regression Gates

- no merge if major findings lose evidence references
- no merge if extraction success rate drops below agreed fixture baseline
- no merge if report required sections are missing

## Production Evolution Path

### V1

- single-process local execution
- local storage only
- CLI-first

### V1.1

- stronger caching
- richer inspection commands
- evaluation harness and baseline metrics

### Later

- API server
- background jobs
- object storage
- Postgres
- multi-user operation if there is real demand

Architectural rule for V1: keep the core pipeline small, typed, and easy to inspect.
