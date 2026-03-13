# Product Requirements Document

## Product Vision

Open Research Agent is an open-source Python system for running bounded research workflows over the public web and user-provided data. A user gives it a question, constraints, and optional files. The system produces a report with traceable evidence, saved intermediate artifacts, and structured outputs for downstream use.

V1 is a research pipeline with agentic decision-making inside a fixed execution path. It is not a general autonomous agent.

## Problem

Teams doing recurring research work usually end up with one of two bad options:

- manual workflows that do not scale and are hard to reproduce
- LLM wrappers that search, summarize, and cite unreliably

The failure modes are consistent:

- search results are not tied to a clear plan
- fetched content is stored inconsistently or not at all
- extracted text is hard to compare across sources
- final answers blur sourced facts, inference, and missing evidence
- there is no clean handoff between web evidence and local datasets

The product should solve this by treating research as a typed pipeline:

1. define a bounded plan
2. gather candidate sources
3. fetch and extract content
4. normalize evidence into consistent records
5. analyze evidence and local tabular inputs
6. produce a report where claims map back to sources

## Product Principles

- `Bounded by default`: every run has a defined objective, constraints, and stopping rules.
- `Evidence first`: major findings must reference evidence records.
- `Inspectable`: each stage persists artifacts that can be reviewed after the run.
- `Python-first`: the core experience should work well from local CLI and script usage.
- `Composable`: search, fetch, extract, analyze, and report stages should be swappable without rewriting the whole system.

## Target Users

### Primary Users

- engineers building research automation tools
- analysts doing market, policy, technical, or competitor research
- founders and product teams validating external claims quickly
- data practitioners combining web evidence with CSV or JSON inputs

### Secondary Users

- open-source contributors extending search, extraction, or analysis modules
- internal platform teams that want to self-host a research service later

## User Jobs

Users need to:

1. submit a focused research question with optional constraints
2. inspect the generated plan before or after execution
3. run discovery over the web without unbounded browsing
4. collect readable content from target pages with usable metadata
5. merge extracted web evidence with local structured data
6. review findings, citations, limitations, and open questions
7. export both human-readable and machine-readable outputs

## Core V1 Workflow

### 1. Request Intake

Input fields:

- research objective
- optional sub-questions
- domain allowlist or denylist
- time horizon or recency preference
- local file paths for CSV or JSON inputs
- output format preference

### 2. Plan

The system generates a serializable plan that includes:

- sub-questions
- search queries
- expected evidence types
- source budget
- stop conditions

### 3. Discovery

The system runs search queries and produces a ranked candidate source list with:

- query provenance
- result rank
- normalized URL
- domain
- reason for inclusion

### 4. Acquisition

The system fetches candidate pages using HTTP first and browser rendering only when required.

Stored artifacts:

- response metadata
- raw HTML
- fetch errors
- final URL after redirects

### 5. Extraction and Normalization

The system extracts main content and converts it into:

- source records
- document records
- evidence records with provenance
- normalized metadata such as title, author, publication date, and content hash

### 6. Analysis

The system performs bounded analysis such as:

- cross-source comparison
- contradiction and agreement detection
- simple tabular analysis over local files
- finding generation tied to evidence IDs

### 7. Report

The system produces:

- Markdown report
- JSON result object
- artifact bundle for inspection and replay

## Core User-Facing Commands

V1 should support these primary CLI workflows:

- `ora plan --objective "..."`
- `ora run --objective "..." --max-sources 10`
- `ora inspect --run-id <run_id> --artifact evidence`
- `ora report --run-id <run_id> --format markdown`
- `ora runs`

These commands define the minimum product surface for launch.

## V1 Outputs

### Markdown Report

The report must contain:

- objective
- scope and constraints
- method summary
- findings
- supporting evidence references
- limitations
- open questions

### JSON Result

The JSON output must contain:

- request metadata
- plan
- sources
- evidence records
- findings
- report sections
- run stats

### Stored Run Artifacts

Each run must persist:

- request payload
- plan
- search results
- fetch outputs
- extracted documents
- normalized evidence
- final report

## Proposed Product Data Objects

These are the core product-level objects the user experience depends on:

- `ResearchRequest`
- `ResearchPlan`
- `CandidateSource`
- `FetchedDocument`
- `ExtractedDocument`
- `EvidenceRecord`
- `Finding`
- `Report`
- `RunSummary`

Each object should have:

- stable IDs
- `run_id`
- timestamps where relevant
- error state where relevant
- enough metadata for inspection from CLI without reading raw artifacts

## Non-Goals

V1 will not include:

- open-ended autonomous task execution
- long-term memory across unrelated runs
- multi-agent orchestration
- browser-assistant or chat-assistant UX
- collaborative workspace features
- production-scale distributed crawling
- enterprise auth, billing, or governance
- slides, dashboards, or polished presentation layers

V1 should also avoid:

- site-specific scraping logic unless a common extractor fails
- model-heavy orchestration where deterministic code is sufficient
- any feature that requires a hosted service to be useful

## Major Engineering Risks

- search provider dependency may constrain reliability or cost
- extraction quality may be inconsistent across page types
- browser fallback may introduce local setup friction
- evidence lineage may break if models are not enforced early
- report synthesis may over-claim if citation rules are weak

## Success Criteria for V1

### User-Level Success

- a user can install the project locally with documented setup in under 20 minutes
- a user can run one command that completes a research workflow from request to report
- a user can inspect sources, evidence, and artifacts from a completed run without modifying code

### Output Quality

- every major finding in the final report includes at least one evidence reference
- the final report always includes a limitations section and open questions section
- the system supports at least 10 successfully processed sources in a single run
- the system supports at least one local CSV or JSON file in the same run as web evidence

### Reliability

- static-page extraction succeeds on at least 80 percent of a representative fixture set
- rendered-page fallback works on at least one JavaScript-heavy fixture in the evaluation set
- repeated runs on the same fixture set produce the same plan structure and artifact schema
- stage failures are recorded with explicit error states rather than silently skipped

### Engineering Readiness

- all pipeline artifacts are defined as typed models
- CLI and future API use the same core services
- core modules have automated tests for schemas, extraction, normalization, and report grounding
- repository docs are sufficient for an external engineer to start implementation without additional product clarification
