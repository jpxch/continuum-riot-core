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
  "data": {},
  "meta": {
    "requestId": "uuid",
    "apiVersion": "v1",
    "dataVersion": "14.4.1",
    "generatedAt": "2026-02-25T00:00:00+00:00"
  }
}
```

### Raw success responses

- `POST /v1/ddragon/sync` returns a direct JSON object.
- Static asset endpoints (`/champions`, `/items`, `/runes`, `/summoners`) return raw Data Dragon JSON.

### Error responses

- Many route-level errors use `HTTPException(detail={code,message})`.
- Unhandled exceptions use the global 500 format:

```json
{
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
    - `currentPatch`
    - `locale`
    - `ingestionScheduled`
    - `modeAuthorityScheduled`

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

- `GET /modes`
  - `200`: envelope with mode list for current patch
  - `404`: `NO_CURRENT_PATCH`

- `GET /modes/{mode_key}/manifest`
  - `200`: envelope with mode manifest for current patch
  - `404`: `NO_CURRENT_PATCH` or `MODE_NOT_FOUND`

## Notes for Consumers

- Response envelopes are not fully standardized yet across every endpoint.
- Some endpoints return raw JSON today; do not assume `meta` is always present.
- Contract/pagination/deprecation policy is planned but not finalized.

## Verification Notes

- Verified locally on 2026-03-12: classifier tests pass, but mode API tests currently hang under `pytest`.
- Verified on 2026-03-12: the Mini host is reachable over SSH, but the deployed service is not currently accepting HTTP connections on port `8000`.
