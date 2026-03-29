# API

## Base

- Base prefix: `/v1`
- Request correlation: `x-request-id` is accepted and echoed in responses.
- Deployment target: `continuum-mini` (`192.168.0.74`)

## Response Shapes

### Envelope-style success responses

Used by endpoints implemented through `success_response(...)`:

```json
{
  "status": "success",
  "data": {},
  "meta": {
    "requestId": "uuid",
    "apiVersion": "v1",
    "dataVersion": "14.4.1",
    "generatedAt": "2026-02-25T00:00:00+00:00"
  }
}
```

### Current success behavior

- `POST /v1/ddragon/sync` uses the shared `success_response(...)` envelope.
- Static asset endpoints (`/champions`, `/items`, `/runes`, `/summoners`) also currently return through `success_response(...)`, with the raw Data Dragon payload nested inside `data`.

### Error responses

- Many route-level errors use `HTTPException(detail={code,message})`.
- Unhandled exceptions use the global 500 format:

```json
{
  "status": "error",
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred.",
    "requestId": "uuid"
  }
}
```

## Endpoint Inventory

### Health and Version

- `GET /v1/health`
  - `200`: service health envelope with `data.status = "ok"`.

- `GET /v1/version`
  - `200`: service info envelope with optional `meta.dataVersion` from current patch.

### Patch and Static Data

- `POST /v1/ddragon/sync`
  - `200`: schedules background ingestion for latest patch and returns:
    - `status`
    - `data.currentPatch`
    - `data.locale`
    - `data.ingestionSchedules`
    - `data.modeAuthoritySchedules`
    - `meta.dataVersion`

- `GET /v1/patch`
  - `200`: envelope with:
    - `currentPatch`
    - `locale` (from `DEFAULT_LOCALE`)
    - `assets` readiness map
  - `404`: `NO_CURRENT_PATCH`

- `GET /v1/champions`
- `GET /v1/items`
- `GET /v1/runes`
- `GET /v1/summoners`
  - `200`: raw asset JSON payload
  - `404`: `NO_CURRENT_PATCH`
  - `409`: `ASSET_NOT_READY`
  - `500`: `FILE_MISSING` or `INVALID_JSON`

### Modes

- `GET /v1/modes`
  - `200`: envelope with mode list for current patch
  - `404`: `NO_CURRENT_PATCH`

- `GET /v1/modes/{mode_key}/manifest`
  - `200`: envelope with mode manifest for current patch
  - `404`: `NO_CURRENT_PATCH` or `MODE_NOT_FOUND`

## Notes for Consumers

- Response envelopes are closer to standardization now, but route-level `HTTPException` responses still differ from the global unhandled-error format.
- The current code-level success helper includes top-level `status`, `data`, and `meta`.
- Contract/pagination/deprecation policy is planned but not finalized.

## Verification Notes

- Verified on 2026-03-29: `continuum-mini` reports `continuum-riot-core.service` as active.
- Verified on 2026-03-29 from the Mini host itself:
  - `GET http://127.0.0.1:8000/v1/health` returns `200`
  - `GET http://127.0.0.1:8000/v1/version` returns `200` with `dataVersion: "16.6.1"`
- Verified on 2026-03-29 from the Mini host itself:
  - `POST http://127.0.0.1:8000/v1/ddragon/sync` returns `200`
  - The observed response body uses the shared success envelope with `status: "success"`, `data.currentPatch: "16.6.1"`, `data.locale: "en_US"`, `data.ingestionSchedules: true`, and `data.modeAuthoritySchedules: true`
  - Service logs record `Mode authority sync complete` for patch `16.6.1`
- Verified on 2026-03-29: route wiring still exposes mode endpoints under the `/v1` API prefix.
- Verified on 2026-03-29 in the Mini workspace: `pytest` reports `11 passed, 1 warning in 0.24s`.
