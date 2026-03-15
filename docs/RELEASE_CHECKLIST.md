# v0.1 Release Checklist

- [ ] Configuration validation passes with default settings.
- [ ] Runs directory is writable and artifacts persist locally.
- [ ] CLI checks: `health`, `research`, `get`, `list`, `artifacts`.
- [ ] API checks: `/health`, `/ready`, `/runs`, `/runs/{id}`, `/runs/{id}/artifacts`.
- [ ] Report and final result artifacts are generated per run.
- [ ] Test suite passes locally (`pytest -q`).
- [ ] Package metadata and README reflect `v0.1.0` MVP hardened status.
- [ ] Deferred limitations reviewed and documented.
