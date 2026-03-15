# Testing Guide

## Run all tests

```bash
pytest -q
```

## Coverage intent for MVP hardening

- Workflow happy path and bounded behavior.
- API health/ready/runs/list/artifacts endpoints.
- CLI research/get/list/artifacts commands.
- Persistence artifact creation/listing.
- Extraction behavior over small deterministic fixtures.
- Browser fallback decision behavior via mocks.
- Config/bootstrap validation.

## Determinism notes

- Search providers are mocked in CLI/API/workflow tests.
- HTTP fetch tests mock `httpx.AsyncClient`.
- Fixtures live in `tests/fixtures/html/` and are intentionally small.
