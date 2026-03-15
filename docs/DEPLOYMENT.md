# Deployment (Local MVP)

## Goal

Run the API as a single packaged service with deterministic local persistence and fail-fast startup validation.

## Local Packaged Flow

1. Provide a `.env` file (optional, but recommended).
2. Build image:
   - `docker build -t open-research-agent:local .`
3. Run image with mounted persistence:
   - `docker run --rm -p 8000:8000 --env-file .env -v "$(pwd)/outputs:/app/outputs" open-research-agent:local`

Or run with compose:

- `docker compose up --build`

## Startup Validation

During bootstrap, runtime validates:

- settings shape and values (environment, host, port, log level, service mode)
- provider-required credentials when applicable (`ORA_SEARCH_API_KEY` for `serpapi`/`tavily`)
- local output directory creation and writability checks

If any validation fails, API/CLI startup fails early with explicit error context.

## Persistence Path Expectations

Default root path is `outputs/` (or `ORA_DATA_DIR` if set).

Prepared paths:

- `runs/`
- `artifacts/`
- `reports/`
- `metadata/`

In containers, mount host storage to `/app/outputs` for predictable persistence.

## Health Endpoints

- `/health`: liveness
- `/ready`: readiness, including validated writable paths and startup bootstrap status

## Troubleshooting

- **Invalid host/port/log level/env values**: verify `ORA_*` variable values against allowed ranges.
- **Readiness reports not ready**: check startup logs for bootstrap errors.
- **Directory not writable**: ensure mounted output directory permissions allow write by container user.
- **Search provider validation failure**: set `ORA_SEARCH_API_KEY` for providers that require it.

## Deferred Beyond MVP

- HA deployment topologies
- distributed workers and queue-based execution
- external DB state persistence
- Kubernetes/cloud platform manifests
