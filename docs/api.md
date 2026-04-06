# API

## Base

- Base prefix: `/v1`
- Request correlation: `x-request-id` is accepted and echoed in responses.
- Deployment target: `continuum-mini` (`192.168.0.74`)

## Response Shapes

### Success envelope

Endpoints implemented through `success_response(...)` return:

```json
{
  "status": "success",
  "data": {},
  "meta": {
    "requestId": "uuid",
    "apiVersion": "v1",
    "dataVersion": "16.6.1",
    "generatedAt": "2026-04-04T00:00:00+00:00"
  }
}
```

Notes:

- `meta.dataVersion` is patch-aware for patch, mode, and sync responses.
- Some endpoints add extra `meta` fields. Example: `/v1/jobs/recent` adds `limit`, `offset`, and `total`.
- Static asset endpoints (`/champions`, `/items`, `/runes`, `/summoners`) return their asset payload inside `data`; they do not return raw top-level JSON anymore.

### Error envelope

Route-level `HTTPException(detail={"code", "message"})` responses and unhandled exceptions are normalized by `app.main` into:

```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable description.",
    "requestId": "uuid"
  }
}
```

Notes:

- Most explicit route errors use stable `code` values such as `NO_CURRENT_PATCH`, `MODE_NOT_FOUND`, `INVALID_JOB_TYPE`, or `JOB_NOT_FOUND`.
- Unhandled exceptions return `INTERNAL_ERROR`.

## Endpoint Inventory

### Health and Version

#### `GET /v1/health`

- `200`: success envelope with `data.status = "ok"`

#### `GET /v1/version`

- `200`: success envelope with:
  - `data.service`
  - `data.env`
  - `meta.dataVersion` set to the current patch when one is registered

### Patch and Static Data

#### `POST /v1/ddragon/sync`

Query params:

- `locale` optional, defaults to `DEFAULT_LOCALE`

Returns:

- `200`: success envelope with:
  - `data.currentPatch`
  - `data.locale`
  - `data.ingestionSchedules = true`
  - `data.modeAuthoritySchedules = true`
  - `meta.dataVersion` set to the latest patch

Behavior:

- Updates the current patch record before scheduling background ingestion.
- Schedules the static-ingestion job and mode sync in the background.

#### `GET /v1/patch`

- `200`: success envelope with:
  - `data.currentPatch`
  - `data.locale`
  - `data.assets` readiness map
  - `meta.dataVersion` set to the current patch
- `404`: `NO_CURRENT_PATCH`

#### `GET /v1/champions`
#### `GET /v1/items`
#### `GET /v1/runes`
#### `GET /v1/summoners`

- `200`: success envelope with the asset JSON nested under `data`
- `404`: `NO_CURRENT_PATCH`
- `409`: `ASSET_NOT_READY`
- `500`: `FILE_MISSING` or `INVALID_JSON`

### Modes

#### `GET /v1/modes`

- `200`: success envelope with the current-patch mode list in `data`
- `404`: `NO_CURRENT_PATCH`

#### `GET /v1/modes/{mode_key}/manifest`

- `200`: success envelope with the current-patch mode manifest in `data`
- `404`: `NO_CURRENT_PATCH`
- `404`: `MODE_NOT_FOUND`

### Jobs

The jobs surface exposes background job outcomes recorded in `job_run_registry`. It is currently the main API-visible observability surface for ingestion runs and supports both per-run inspection and aggregate failure/summary views.

#### `GET /v1/jobs/recent`

Query params:

- `limit` optional, default `10`, capped at `100`
- `offset` optional, default `0`, must be `>= 0`
- `job_type` optional, current allowlist: `ddragon_sync`
- `status` optional, current allowlist: `success`, `failed`, `running`

Returns:

- `200`: success envelope with:
  - `data[]` entries containing:
    - `id`
    - `job_type`
    - `status`
    - `patch`
    - `duration_ms`
    - `assets`
    - `started_at`
    - `finished_at`
  - `meta.limit`
  - `meta.offset`
  - `meta.total`

Errors:

- `400`: `INVALID_OFFSET`
- `400`: `INVALID_STATUS`
- `400`: `INVALID_JOB_TYPE`

#### `GET /v1/jobs/latest`

Query params:

- `job_type` required, current allowlist: `ddragon_sync`

Returns:

- `200`: success envelope with:
  - `data.id`
  - `data.job_type`
  - `data.job_key`
  - `data.status`
  - `data.error`
  - `data.started_at`
  - `data.finished_at`
  - `data.patch`
  - `data.locale`
  - `data.duration_ms`
  - `data.assets`
  - `data.metadata`

Errors:

- `400`: `INVALID_JOB_TYPE`
- `404`: `JOB_NOT_FOUND`

#### `GET /v1/jobs/summary`

Query params:

- `job_type` optional, current allowlist: `ddragon_sync`

Returns:

- `200`: success envelope with:
  - `data.total`
  - `data.success`
  - `data.failed`
  - `data.running`
  - `data.avg_duration_ms`

Interpretation:

- `total` is the number of recorded jobs in scope.
- `success`, `failed`, and `running` are counts by terminal or active state.
- `avg_duration_ms` averages only completed jobs with status `success` or `failed`; running jobs are excluded.
- Empty result sets return zeros rather than `null`.

Errors:

- `400`: `INVALID_JOB_TYPE`

#### `GET /v1/jobs/failures`

Query params:

- `job_type` optional, current allowlist: `ddragon_sync`

Returns:

- `200`: success envelope with:
  - `data.total_failures`
  - `data.by_error[]` entries containing:
    - `error`
    - `count`

Interpretation:

- Only jobs with `status = "failed"` are included.
- `total_failures` is the sum of all grouped failure counts in scope.
- `by_error` is grouped by `error_message` and sorted by descending count.
- Missing or empty stored failure messages are normalized to `"unknown"` in the response.

Errors:

- `400`: `INVALID_JOB_TYPE`

#### `GET /v1/jobs/{job_id}`

Path params:

- `job_id` required UUID

Returns:

- `200`: success envelope with the same payload shape as `/v1/jobs/latest`

Errors:

- `404`: `JOB_NOT_FOUND`

## Notes for Consumers

- The current API surface is consistently envelope-based for both success and error responses.
- `meta.dataVersion` is meaningful for patch-driven content and may be `null` for operational endpoints such as jobs.
- Use `/v1/jobs/recent` for timeline-style support/debug views, `/v1/jobs/latest` and `/v1/jobs/{job_id}` for single-run inspection, `/v1/jobs/summary` for health snapshots, and `/v1/jobs/failures` for repeated-error triage.
- The current `job_type` allowlist is intentionally narrow. Consumers should treat it as a validated enum rather than assuming arbitrary future values will be accepted.
- The jobs endpoints are useful for ingestion visibility, but broader versioning, pagination, and deprecation policy is still being formalized.

## Verification Notes

- Verified on 2026-03-29: `continuum-mini` reports `continuum-riot-core.service` as active.
- Verified on 2026-03-29 from the Mini host itself:
  - `GET http://127.0.0.1:8000/v1/health` returns `200`
  - `GET http://127.0.0.1:8000/v1/version` returns `200` with `dataVersion: "16.6.1"`
- Verified on 2026-03-30 from the Mini host itself:
  - `POST http://127.0.0.1:8000/v1/ddragon/sync` returns `200`
  - The observed response body uses the shared success envelope with `status: "success"`, `data.currentPatch: "16.6.1"`, `data.locale: "en_US"`, `data.ingestionSchedules: true`, and `data.modeAuthoritySchedules: true`
  - Service logs record `Mode authority sync complete` for patch `16.6.1`
- Verified on 2026-03-29: route wiring exposes health, version, ddragon, static, modes, and jobs endpoints under the `/v1` prefix.
- Verified on 2026-04-04 in the local workspace:
  - `TMPDIR=/dev/shm .venv/bin/pytest -q tests/test_jobs.py` reports `10 passed, 1 warning`
  - `TMPDIR=/dev/shm .venv/bin/pytest -q` reports `24 passed, 1 warning`
