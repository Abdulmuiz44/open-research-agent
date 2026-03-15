# Changelog

## [0.1.0] - 2026-03-15

### Added
- v0.1 MVP release baseline with bounded CLI/API workflow, local artifact persistence, deterministic report generation, and run retrieval/artifact listing.
- API readiness endpoint (`GET /ready`) for release-path checks.
- Storage rehydration from persisted `manifest.json` so run retrieval works across process restarts in local MVP mode.
- Release documentation set for v0.1 (`docs/RELEASE_CHECKLIST.md`, `docs/RELEASE_NOTES_V0_1.md`).

### Changed
- `analysis/final_result.json` now includes consistent release-critical metadata: objective/query, timestamps, source/extraction counts, findings/themes counts, artifact dir/count, and report path.
- Improved API 404 messages for missing runs.
- Updated `.env.example` and `README.md` to match actual v0.1 configuration keys, paths, and commands.

### Fixed
- FastAPI startup deprecation warning by moving startup logging from `@app.on_event("startup")` to lifespan handler.
