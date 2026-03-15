# v0.1 Release Checklist

## Product Scope
- [ ] MVP scope matches `docs/MVP_SCOPE.md` (no out-of-scope features added).
- [ ] Deferred features are explicitly documented.

## Runtime Validation
- [ ] CLI health command passes.
- [ ] API health and readiness endpoints pass.
- [ ] One end-to-end run can be created and retrieved.
- [ ] Run artifacts can be listed and inspected under `outputs/runs/<run_id>/`.

## Artifact Consistency
- [ ] `manifest.json` includes core run metadata and artifact paths.
- [ ] `analysis/final_result.json` includes run id, status, objective/query, timestamps, key counts, and report path.
- [ ] `report/report.md` is present for completed runs.

## Documentation and Metadata
- [ ] `README.md` matches current CLI/API behavior.
- [ ] `.env.example` matches `src/core/config.py` settings.
- [ ] `CHANGELOG.md` includes 0.1.0 release notes.
- [ ] Package version is `0.1.0` in `pyproject.toml`.

## Test Gate
- [ ] Full test suite passes locally (`pytest -q`).
- [ ] Critical workflow tests cover happy path, fallback placeholder, run retrieval, artifact listing, health/readiness, and config defaults.
