# MVP Scope

## Scope Statement

V1 is a local, CLI-first research pipeline that answers a bounded question using web evidence and optional local tabular inputs. It stores its intermediate artifacts and produces a grounded report with citations.

If a feature does not directly improve that path, it is out of scope for V1.

## V1 Includes

### Required User Capability

The user can:

- provide a research objective and basic constraints
- run a single command to execute the pipeline
- inspect the saved plan, sources, evidence, and report after the run
- export Markdown and JSON outputs

### Required Pipeline Stages

V1 includes exactly these stages:

1. request intake
2. planning
3. search
4. fetch
5. extract
6. normalize
7. analyze
8. report
9. storage and inspection

### Supported Inputs

- web pages discovered through search
- local CSV files
- local JSON files

Parquet may be supported internally for artifact storage, but user-facing parquet ingestion is not required for launch.

### Required Outputs

- Markdown report
- JSON result
- stored run artifacts on disk

### Required Operational Behavior

- HTTP fetch as the default path
- browser rendering only as fallback
- evidence IDs carried from normalization through reporting
- explicit error recording at each stage

## Concrete V1 Deliverables

These items should exist by launch:

- working CLI commands for `run`, `plan`, `inspect`, `report`, and `runs`
- typed models for request, plan, source, fetch, extract, evidence, finding, and report
- local storage layout with `SQLite` plus per-run artifacts on disk
- one search provider adapter
- one LLM provider adapter through `LiteLLM`
- one end-to-end example run documented in the repo
- one evaluation fixture set with expected outputs

## V1 Excludes

### Product Exclusions

- general autonomous agent behavior
- open-ended browsing without a source budget
- chat UI, desktop UI, or web app UI
- long-term memory across runs
- collaborative workspaces
- scheduling or recurring jobs
- human approval workflows inside the pipeline

### Technical Exclusions

- distributed crawling
- queue workers
- multi-agent orchestration
- vector retrieval as a core dependency
- OCR and PDF-first ingestion pipelines
- enterprise deployment features
- custom model training or ranking models

### Output Exclusions

- dashboards
- slide generation
- presentation-quality narrative formatting beyond Markdown

## Technical Boundaries

V1 should stay within these limits:

- single machine
- single-process execution
- one bounded run at a time from the CLI
- English-first extraction and reporting
- source budget per run set by the planner
- article and documentation page support first; broad site crawling later

V1 should optimize for:

- reliability on common web pages
- predictable artifact schemas
- grounded findings
- ease of contribution

V1 should not optimize for:

- maximal page coverage
- autonomous exploration depth
- hosted scale

## Environment and Dependency Expectations

V1 should assume:

- Python 3.12+
- `uv` for dependency management
- `Playwright` installed locally when browser fallback is enabled
- one configured LLM model for planning and synthesis
- one configured search provider

Recommended environment variables:

- `OPENAI_API_KEY`
- `LITELLM_MODEL`
- `SEARCH_API_KEY`
- `ORA_DATA_DIR`
- `ORA_ENABLE_BROWSER_FALLBACK`
- `ORA_MAX_SOURCES_DEFAULT`

## Launch Criteria

V1 launches when all of these are true:

- CLI setup and first run are documented
- at least one end-to-end example works from request to report
- the pipeline handles at least 10 sources in a run
- the pipeline handles at least one static page fixture and one rendered-page fixture
- the pipeline ingests at least one CSV or JSON file during a run
- the final report includes citations, limitations, and open questions
- intermediate artifacts can be inspected after execution
- automated tests cover core schemas and critical pipeline paths

## Engineering Priorities

Priority order:

1. artifact contracts and typed schemas
2. fetch and extraction reliability
3. evidence grounding and report quality
4. CLI usability and inspection flows
5. evaluation coverage and regression protection

Decision rule:

When choosing between broader capability and tighter reliability, prefer tighter reliability.

## Major Engineering Risks

- provider lock-in sneaking into core services
- fetch and extraction variability across site types
- weak evidence lineage causing uncited findings
- storage layout instability creating migration churn during initial development
- browser fallback becoming too expensive to use as a default path

## Testing Strategy for Scope Enforcement

V1 testing should enforce the scope boundary, not just code correctness.

- run fixture-based extraction tests on every pull request
- run at least one end-to-end pipeline test with web-like fixtures and local file inputs
- verify that reports always include required sections
- verify that major findings always include evidence IDs
- verify that disabled features such as PDF ingestion and vector retrieval are not required by the happy path

## Roadmap Beyond V1

### V1.1

- caching and retry improvements
- richer inspect commands
- better extraction coverage for tables and edge-case layouts
- evaluation harness with baseline metrics

### V1.2

- API surface over the same pipeline core
- background execution model
- object storage support

### Later Versions

- scheduled runs
- reusable knowledge across related runs
- human review checkpoints
- more advanced source quality heuristics

## Explicit Scope Cuts

To avoid scope creep, V1 will not add the following unless the launch criteria are already met:

- PDF ingestion
- spreadsheet-specific preprocessing beyond normal CSV handling
- domain-specific extractors
- vector search
- browser automation beyond page render and content retrieval
