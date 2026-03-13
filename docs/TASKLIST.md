# Task List

## Execution Rules

- build the narrowest end-to-end path first
- lock schemas before adding feature breadth
- persist artifacts at every stage
- evaluate quality with fixtures, not intuition
- do not add API or UI work before the CLI path is stable

## File-by-File Build Order

Build in this order so the dependency graph stays clean:

1. `pyproject.toml`
2. `src/open_research_agent/config.py`
3. `src/open_research_agent/errors.py`
4. `src/open_research_agent/core/models/run.py`
5. `src/open_research_agent/core/models/request.py`
6. `src/open_research_agent/core/models/plan.py`
7. `src/open_research_agent/core/models/source.py`
8. `src/open_research_agent/core/models/fetch.py`
9. `src/open_research_agent/core/models/extract.py`
10. `src/open_research_agent/core/models/evidence.py`
11. `src/open_research_agent/core/models/finding.py`
12. `src/open_research_agent/core/models/report.py`
13. `src/open_research_agent/storage/db.py`
14. `src/open_research_agent/storage/artifacts.py`
15. `src/open_research_agent/storage/repositories/runs.py`
16. `src/open_research_agent/core/services/pipeline.py`
17. `src/open_research_agent/core/services/planner.py`
18. `src/open_research_agent/providers/search/base.py`
19. `src/open_research_agent/providers/search/<provider_name>.py`
20. `src/open_research_agent/core/services/search.py`
21. `src/open_research_agent/providers/browser/playwright_fetcher.py`
22. `src/open_research_agent/core/services/fetcher.py`
23. `src/open_research_agent/providers/extraction/trafilatura_extractor.py`
24. `src/open_research_agent/providers/extraction/selectolax_fallback.py`
25. `src/open_research_agent/core/services/extractor.py`
26. `src/open_research_agent/core/services/normalizer.py`
27. `src/open_research_agent/core/services/analyzer.py`
28. `src/open_research_agent/core/services/reporter.py`
29. `src/open_research_agent/cli/app.py`
30. `src/open_research_agent/cli/commands/run.py`
31. `src/open_research_agent/cli/commands/plan.py`
32. `src/open_research_agent/cli/commands/inspect.py`
33. `src/open_research_agent/cli/commands/report.py`
34. `tests/unit/...`
35. `tests/integration/...`

Rule:

- do not implement CLI or API wrappers before the pipeline services and storage contracts exist

## Phase 0: Product and Artifact Contracts

- finalize the V1 launch criteria from `docs/MVP_SCOPE.md`
- define the canonical run stages and artifact boundaries
- define Pydantic models for request, plan, candidate source, fetched document, extracted document, evidence record, finding, and report
- define required fields for provenance, citations, and error states
- decide the run directory layout and SQLite table set
- define the first evaluation fixture set for static pages, rendered pages, and mixed-input tasks

### Milestone

- artifact contracts are frozen enough to start implementation

### Blockers To Watch

- changing core schemas after multiple modules are already built
- unclear distinction between source, document, and evidence records

## Phase 1: Repository and Tooling Setup

- initialize the project with `uv`
- create `pyproject.toml` with runtime and development dependencies
- configure `Ruff` and `Pytest`
- create the package layout for `core`, `pipeline`, `storage`, `cli`, and `tests`
- implement config loading from environment variables
- add a minimal CLI entrypoint with placeholder commands
- add test fixtures and fixture-loading helpers

### Milestone

- repository installs cleanly and test tooling runs locally

### Blockers To Watch

- package layout coupled too tightly to a future API
- missing fixtures leading to untestable implementation work

## Phase 2: Storage and Run Lifecycle

- implement the run storage service
- create SQLite tables for run metadata and stage records
- implement artifact write and read helpers for JSON, HTML, Markdown, and Parquet
- implement run initialization and finalization flows
- add inspection helpers for loading a run and enumerating artifacts
- test persistence and replay of partial and completed runs

### Milestone

- a run can be created, persisted, reloaded, and inspected without pipeline logic

### Blockers To Watch

- storage decisions made too late, forcing stage rewrites
- run IDs or artifact paths that are not stable enough for inspection

## Phase 3: Request Intake and Planning

- implement request validation and constraint handling
- implement planner service that produces sub-questions, search queries, source budget, and stop conditions
- wire the planner to the selected LLM provider abstraction
- persist the request and plan artifacts
- add tests for plan structure determinism and schema validity

### Milestone

- a user request can be turned into a stored bounded plan

### Blockers To Watch

- planning logic drifting into autonomous looping
- vague plan outputs that are not actionable for search

## Phase 4: Search and Source Selection

- define the search provider interface
- implement the first search adapter
- implement URL normalization, deduplication, and source ranking
- preserve query provenance on every candidate source
- persist search results and selected sources
- add tests for deduplication and ranking behavior

### Milestone

- the system can produce a bounded set of candidate sources from a plan

### Blockers To Watch

- search provider instability blocking progress
- losing the mapping from plan query to selected source

## Phase 5: Fetch and Extract

- implement the HTTP fetcher with retries, headers, and timeout policies
- implement browser-rendered fallback with `Playwright`
- persist raw HTML, fetch metadata, and fetch failures
- implement extraction with `Trafilatura`
- implement extraction fallback with `Selectolax`
- normalize core document metadata such as title, canonical URL, author, and publication date
- add fixture-based tests for static and rendered pages

### Milestone

- representative pages can be fetched and converted into extracted documents

### Blockers To Watch

- browser fallback becoming the default code path
- extraction quality relying on brittle per-site rules

## Phase 6: Normalize and Analyze

- implement source, document, and evidence normalization
- generate stable IDs for evidence and sources
- implement CSV and JSON ingestion
- standardize mixed evidence into a single analysis-ready layer
- implement lightweight analysis for synthesis, comparison, contradiction detection, and basic tabular summaries
- persist normalized evidence and analysis artifacts
- add tests that verify findings always reference evidence IDs

### Milestone

- extracted content and local structured inputs can produce grounded findings

### Blockers To Watch

- findings generated without clear evidence linkage
- normalization layer leaking extraction-specific assumptions

## Phase 7: Report and Inspection UX

- define the final report schema and required sections
- implement Markdown report rendering
- implement JSON result rendering
- render citations from evidence IDs back to source metadata
- implement CLI inspection commands for runs, sources, evidence, and findings
- add tests for report completeness and citation coverage

### Milestone

- the user can run the pipeline and inspect a grounded result from the CLI

### Blockers To Watch

- report output masking uncertainty or missing evidence
- inspection commands reading directly from ad hoc files instead of storage interfaces

## Phase 8: Hardening and Launch Prep

- add stage-level metrics and timing capture
- improve error taxonomy and retry behavior
- run the evaluation fixture set and record baseline results
- document local setup, example runs, and contribution workflow
- verify launch criteria from `docs/MVP_SCOPE.md`
- remove or defer any feature that threatens the launch path

### Milestone

- V1 is ready for external evaluation by early users and contributors

### Blockers To Watch

- no baseline metrics for extraction and grounding quality
- scope creep into API, UI, or advanced automation before launch

## Week 1 to Week 4 Sequence

## Week 1

- freeze artifact contracts and launch criteria
- initialize the repo, tooling, and package layout
- implement config loading and storage primitives
- implement run lifecycle basics
- create the first fixture set

### Week 1 Deliverable

- installable repo with schemas, config, storage skeleton, and test scaffolding

## Week 2

- implement request intake and planner
- implement search provider abstraction and first adapter
- persist plan and search artifacts
- test determinism, deduplication, and provenance tracking

### Week 2 Deliverable

- request-to-candidate-source path working end to end

## Week 3

- implement fetch and browser fallback
- implement extraction and metadata normalization
- persist raw and cleaned document artifacts
- validate against static and rendered-page fixtures

### Week 3 Deliverable

- candidate-source-to-extracted-document path working reliably

## Week 4

- implement normalization, analysis, and report generation
- implement CSV and JSON ingestion
- add inspect commands
- run the evaluation set and tighten weak areas
- complete setup and example documentation

### Week 4 Deliverable

- end-to-end MVP path from request to grounded report

## Example CLI Commands To Validate During Build

- `ora plan --objective "Compare AI search APIs for research tooling"`
- `ora run --objective "Summarize open-source web extraction libraries" --max-sources 10`
- `ora run --objective "Compare public pricing pages" --input-file tests/fixtures/files/pricing_targets.csv`
- `ora inspect --run-id <run_id> --artifact findings`
- `ora report --run-id <run_id> --format json`

## Example API Endpoints To Keep In Mind

These are not V1 deliverables, but the service layer should make them easy later:

- `POST /plan`
- `POST /runs`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/sources`
- `GET /runs/{run_id}/evidence`
- `GET /runs/{run_id}/report`

## Milestones Summary

- M1: artifact contracts and launch criteria frozen
- M2: repo and storage foundation complete
- M3: planning and search working
- M4: fetch and extract working
- M5: normalization, analysis, and report working
- M6: launch criteria verified

## Metrics To Track During Build

- plan generation success rate
- candidate-source count per run
- fetch success rate
- extraction success rate
- percentage of findings with evidence references
- end-to-end success rate on evaluation fixtures

## Testing Strategy for V1

### Unit

- model validation
- config loading
- URL normalization
- artifact path generation
- citation enforcement rules

### Integration

- planner with mocked LLM responses
- search with mocked provider responses
- fetch and extract against local HTML fixtures
- normalization and analysis against mixed web and CSV or JSON fixtures

### End-to-End

- one deterministic happy-path research run
- one run that exercises browser fallback
- one run that mixes web evidence with local structured data

### Release Gate

- required report sections present
- all major findings cite evidence
- launch criteria from `docs/MVP_SCOPE.md` pass

## Definition of MVP Complete

- all launch criteria in `docs/MVP_SCOPE.md` are met
- evaluation fixtures run without manual patching
- core failures are inspectable from stored artifacts
- the system is narrow, documented, and ready for external contributors
