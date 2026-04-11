# Architecture

## Service Role

`continuum-riot-core` is a Riot-backed authority service that owns:

- ingestion from Data Dragon (today) and Riot APIs (planned),
- normalization and persistence in Postgres,
- read APIs for downstream consumers.

This repository is not a consumer app UI.

Primary runtime target is `continuum-mini` at `192.168.0.74`.

## Runtime Components

- API framework: FastAPI (`app/main.py`, `app/api/*`)
- Database access: SQLAlchemy async sessions (`app/db/*`)
- Schema migrations: Alembic (`alembic/*`)
- Static asset storage: filesystem under `STATIC_ROOT/<patch>/<locale>/`

## Current Data Domains

- `patch_registry`: tracks discovered patches and current patch.
- `asset_registry`: tracks static asset metadata and checksums.
- `mode_registry`: canonical mode entries.
- `mode_patch_registry`: mode state per patch (`ready`, `partial`, `failed`).
- `mode_queue_binding`: queue-to-mode bindings.
- `job_run_registry`: background job lifecycle and failure metadata.

## Request and Ingestion Flow

1. `POST /v1/ddragon/sync` fetches latest patch from DDragon.
2. The patch is persisted as current in `patch_registry`.
3. A FastAPI background task downloads static JSON files for request-triggered sync.
4. The same background task schedules mode authority sync for the current patch.
5. A lifespan-started patch poller periodically checks DDragon for patch changes and can trigger the same ingest path automatically.
6. Files are written under `STATIC_ROOT/<patch>/<locale>/`.
7. Metadata (sha256, file size, content type) is upserted into `asset_registry`.
8. Job progress and failures are recorded in `job_run_registry`.
9. Read endpoints load from local files and validate readiness via DB metadata.

## Read Flow

- Patch and mode endpoints read normalized DB records and return API envelopes.
- Static endpoints (`/champions`, `/items`, `/runes`, `/summoners`) return raw JSON payloads from disk.

## Cross-Cutting Concerns

- Request IDs: middleware injects/propagates `x-request-id`.
- Logging: JSON logs via stdlib + structlog processors.
- Error handling:
  - route-level `HTTPException` detail payloads for known failures,
  - global 500 handler returns `{ "error": { ... } }`.

## Current Gaps

- Patch poller baseline exists, but richer observability and lifecycle controls are still missing.
- Player identity/match ingestion is intentionally deferred until the DB-backed authority model is designed.
- Live Postgres migration validation should be rechecked when migration or deployment posture changes.
- Mode API tests were rechecked locally in the roadmap refresh and no longer hang in the dev harness.
- Mini deployment is currently healthy under `continuum-riot-core.service` and serves on port `8000`.
