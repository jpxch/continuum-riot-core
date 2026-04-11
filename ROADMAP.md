# Continuum Riot Core Roadmap

Last updated: 2026-04-11

## Purpose (Grounding Contract)

This file is the source-of-truth context for ongoing ChatGPT/Codex sessions.

- `continuum-riot-core` is the Riot-backed data authority server.
- It is not the SoulRift client app; SoulRift is one consumer of this API.
- Authority scope includes:
  - static game data across all live modes (SR, ARAM, TFT, rotating seasonal modes)
  - player data pulled from Riot APIs (identity, match history, factual item/rune/summoner snapshots)
- The server owns ingestion, normalization, storage, and read APIs for downstream clients.
- The server should expose durable, queryable facts rather than product-specific companion app behavior.
- Build recommendation, build classification, gameplay advice, lore interpretation, and other intelligence layers are out of scope for the core authority service unless explicitly reframed as factual stored data quality/enrichment.
- Keep phase status aligned with real code in the repo and current working tree.

## Deployment Target (Current)

- Primary runtime target is the Mini host `continuum-mini` at `192.168.0.74`.
- Runtime binding and DSNs remain environment-driven (`HOST`, `PORT`, `DATABASE_URL`, `DATABASE_URL_SYNC`).
- Keep deployment docs/config host-specific, but keep code paths environment-portable.

## Verified Status Snapshot

Validated from the repo and current working tree on 2026-04-10 unless otherwise noted. Boundary and git-status notes were refreshed on 2026-04-11:

- Active branch is `feature/player-ingestion`.
- `git log -1 --oneline` reports `149f8ff` (`fix: correct typo in game mode key in transform_match function`).
- `git status --short --untracked-files=all` shows `.gitignore` modified and `ROADMAP.md` now visible as untracked.
- `.env.example` exists and the repo still expects the baseline env vars (`DATABASE_URL`, `DATABASE_URL_SYNC`, `RIOT_API_KEY`, service/API settings).
- `app/api/response.py` now wraps both success and error payloads with a top-level `status` field.
- Route wiring still exposes the implemented API under the `/v1` prefix.
- Route wiring also includes the jobs router, so `/v1/jobs/recent`, `/v1/jobs/latest`, and `/v1/jobs/{job_id}` are live in the repo API surface.
- The prototype players router has been removed from stable `/v1` route wiring; player/match authority work is deferred until it is backed by persisted player/match records.
- `app/api/router.py` remains the concrete source of route composition for the `/v1` surface.
- `app/main.py` still starts the patch poller from FastAPI lifespan when `ENABLE_PATCH_POLLER` is enabled.
- `app/services/http_client.py` still provides the shared outbound HTTP baseline:
  - `HTTP_TIMEOUT_SECONDS`
  - `HTTP_MAX_RETRIES`
  - `HTTP_RETRY_BACKOFF_SECONDS`
- `app/services/ddragon.py` and `app/services/queue_catalog.py` still use the shared HTTP client helpers.
- `app/services/static_ingestion.py` still raises a terminal `RuntimeError` when asset ingestion fails.
- The repo includes the current automated test set:
  - `tests/test_contract.py`
  - `tests/test_http_client.py`
  - `tests/test_jobs.py`
  - `tests/test_mode_classifier.py`
  - `tests/test_modes_read.py`
  - `tests/test_mode_manifest.py`
  - `tests/test_static_ingestion.py`
- Dedicated endpoint tests exist for the `/v1/jobs/*` read surface in `tests/test_jobs.py`.
- `docs/api.md` still does not document the `/v1/jobs/*` endpoints, so the observability surface is implemented before its consumer-facing contract doc.
- `app/api/v1/jobs.py` still raises plain-string `HTTPException.detail` values for validation and not-found cases, so jobs responses are not yet aligned with the `{code, message}` detail shape used by the static and mode routes.
- `/v1/jobs/recent` currently caps `limit` at `100` and validates `offset`, `status`, and `job_type`, but `/v1/jobs/latest` still accepts an unvalidated `job_type` query parameter.
- The `ddragon` response-helper typo is fixed in code: `app/api/v1/ddragon.py` now imports and calls `success_response`.
- Mini workspace verification is green again on 2026-03-29: `pytest` reports `11 passed, 1 warning in 0.24s` from `/mnt/continuum/Projects/continuum-riot-core` on `continuum-mini`.
- Mini host import verification is green on 2026-04-10: `python -c 'import app.main; print("import ok")'` succeeds.
- Alembic migration verification is green on `continuum-mini` on 2026-04-10: `alembic upgrade head` completes without error against Postgres.
- Runtime `/v1` checks are green on `continuum-mini` on 2026-04-10:
  - `GET http://127.0.0.1:8000/v1/health` returns `200`
  - `GET http://127.0.0.1:8000/v1/version` returns `200` with `dataVersion: "16.7.1"`
- Runtime sync smoke is green on `continuum-mini` on 2026-04-10:
  - `POST http://127.0.0.1:8000/v1/ddragon/sync` returns `200`
  - Response body reports `status: "success"`, `currentPatch: "16.6.1"`, `locale: "en_US"`, `ingestionSchedules: true`, and `modeAuthoritySchedules: true`
  - Service logs record `Mode authority sync complete` for patch `16.6.1`
  - `job_run_registry` now records the newest `ddragon_sync` run as `success` with `error_message: null`, asset summary metadata, and `duration_ms`
- The previously failing `ddragon_sync` background path on Mini was re-verified and fixed on 2026-03-30:
  - root cause was `summarize_results()` using a type annotation instead of assigning a dict
  - the fix is committed locally in `70acfdd`
  - Mini service restart and live post-fix smoke verification both completed successfully
- Local `pytest` in this environment still uses `TMPDIR=/dev/shm` to avoid an initial temp-directory startup failure.
- Local verification on 2026-04-10 (non-mode slice): `TMPDIR=/dev/shm .venv/bin/pytest -q tests/test_http_client.py tests/test_mode_classifier.py tests/test_static_ingestion.py` reports `10 passed, 1 warning in 0.09s`.
- Local verification on 2026-04-10 (mode slice): `TMPDIR=/dev/shm .venv/bin/pytest -q tests/test_modes_read.py` reports `2 passed, 1 warning in 0.31s` and `TMPDIR=/dev/shm .venv/bin/pytest -q tests/test_mode_manifest.py` reports `2 passed, 1 warning in 0.24s`.
- Local full-suite verification is green on 2026-04-10 with that workaround: `TMPDIR=/dev/shm .venv/bin/pytest -vv` reports `35 passed, 1 warning in 0.31s`.
- The stale `pythonjsonlogger.jsonlogger` import has been removed from `app/core/logging.py`.
- `continuum-mini` remains the primary deployment target. The remaining runtime gaps are telemetry depth and broader contract hardening rather than startup/import health.

Implemented APIs:

- `GET /v1/health`
- `GET /v1/version`
- `POST /v1/ddragon/sync`
- `GET /v1/patch`
- `GET /v1/champions`
- `GET /v1/items`
- `GET /v1/runes`
- `GET /v1/summoners`
- `GET /v1/modes`
- `GET /v1/modes/{mode_key}/manifest`
- `GET /v1/jobs/recent`
- `GET /v1/jobs/latest`
- `GET /v1/jobs/{job_id}`

Implemented core services:

- Static ingestion + metadata persistence:
  - `app/services/static_ingestion.py`
  - `app/services/static_read.py`
  - `app/core/paths.py`
  - `app/utils/hash.py`
- Mode read services:
  - `app/services/mode_read.py`
  - `app/models/mode.py`
  - `alembic/versions/76cb22759f36_add_mode_registry_tables.py`
- Mode authority write/bootstrap services:
  - `app/services/mode_authority.py`
  - `app/services/mode_seed.py`
  - `app/services/mode_classifier.py`
  - `app/services/queue_catalog.py`
- Job-run tracking services:
  - `app/models/job_run.py`
  - `app/services/job_registry.py`
  - `alembic/versions/a80417ec8616_add_job_run_registry_table.py`
- Shared HTTP client baseline:
  - `app/services/http_client.py`
  - `app/core/config.py`

Current sync path is both request-triggered (`POST /v1/ddragon/sync`) and lifecycle-driven: the app starts a background patch poller on FastAPI lifespan startup via `app/services/patch_poller.py`. The previously noted `ddragon` import typo is now fixed, the Mini workspace `pytest` baseline is green again, the host-local `/v1/health` plus `/v1/version` checks are green on `continuum-mini`, and `POST /v1/ddragon/sync` smoke verification now returns the same success envelope shape as the local code with a matching `Mode authority sync complete` log entry. The repo also now exposes DB-backed job history endpoints for recent/latest/by-id sync outcomes, but those surfaces still need docs, endpoint tests, and consistent error-shape hardening before they can be treated as a stable consumer contract. Treat observability and contract hardening as the immediate stabilization sequence.

## Git Status And Direction

Current git status:

- Active branch: `feature/player-ingestion`
- Working tree: dirty for this roadmap update, `.gitignore` cleanup, and prototype quarantine.
- Latest commit before this roadmap refresh: `149f8ff` (`fix: correct typo in game mode key in transform_match function`)

Required direction:

1. Add ingestion observability beyond the current poller baseline (job telemetry, error surfacing, health visibility).
2. Document and test the existing `/v1/jobs/*` observability surfaces before widening telemetry further.
3. Define Phase 4 consumer contracts (versioning, pagination, error semantics) before starting the player/match foundation phases.
4. Expand sync-path verification from smoke-level success to repeatable contract/idempotency coverage.

## Boundary Reset (2026-04-11)

The codebase briefly started an early player/match prototype before the storage authority model was ready. That prototype has been removed from stable route wiring and the helper files were deleted rather than promoted to the consumer contract.

Prototype files/surfaces removed or deferred until Phase 6A/6B is designed:

- `app/api/v1/players.py` was removed because it fetched Riot matches live and returned transformed data instead of scheduling ingestion and reading from stored records.
- `app/services/player_ingestion.py` was removed because it fetched Riot match IDs and matches directly with a hardcoded regional route and without the shared HTTP client/rate-limit policy.
- `app/services/match_transform.py` was removed because it created an immediate response projection instead of a persistence-oriented snapshot.
- `app/services/champion_transform.py` was removed because it was an orphan transform not wired into static ingestion.
- `app/services/build_classifier.py` was removed because build classification belongs outside the core authority service unless it is reworked into factual snapshot/data-quality enrichment.

Preferred correction:

1. Keep player/match APIs out of the stable consumer API until persistence exists.
2. Make future `POST /v1/players/{puuid}/sync` schedule an ingestion job and return job/readiness status.
3. Make future `GET /v1/players/{puuid}/matches` read from DB-backed match records only.
4. Store raw Riot payload references plus light normalized facts: match ID, patch, queue/mode, participants, champion IDs, spell IDs, rune IDs, item IDs, core stats, timestamps, and sync provenance.
5. Keep recommendations, build classifiers, lane/gameplay advice, and SoulRift-specific response shapes in SoulRift or a separate intelligence service.

## Reality-Checked Phase Status

| Phase | Name | Status | Notes |
|---|---|---|---|
| 0 | Foundation | In Progress | Core app, DB lifecycle, and migration chain are in place. Mini verification is improved again: the `ddragon` import typo is fixed, `pytest` is green in the Mini workspace, host-local `/v1/health` plus `/v1/version` checks are green, and `alembic upgrade head` is green on Mini. |
| 1 | Riot Access & Compliance | In Progress | Shared HTTP retry/backoff/timeout settings and client helpers exist, and the queue catalog uses the shared client baseline. Basic job outcome visibility now exists through `job_run_registry` plus `/v1/jobs/*`, but rate-limit strategy, routing policy, secret hygiene, validation consistency, and richer telemetry are still open. |
| 2 | Patch & Static Data Authority | In Progress | Ingestion + read endpoints are implemented, a patch poller baseline runs on app startup, and `POST /v1/ddragon/sync` is now green on `continuum-mini` through both the HTTP envelope and the recorded `job_run_registry` success outcome. Recent/latest/by-id job status is queryable through the API, so the next confidence step is docs/tests, consistent endpoint behavior, and broader sync-path coverage. |
| 3 | Mode Authority Core | In Progress | Mode schema/models, read APIs, and bootstrap/discovery write workflow are implemented, and the earlier `ddragon` import regression is fixed. The mode API test files were rechecked locally in this refresh and no longer hang, but the full-suite baseline still needs a unified re-run. |
| 4 | Consumer Integration Contracts | In Progress | Shared success/error helpers exist, and `/v1/jobs/recent` now returns pagination metadata while validating `offset`, `status`, and `job_type` and capping `limit` at `100`. Cross-endpoint error, validation, pagination, and deprecation rules are still not standardized enough to treat this phase as complete. |
| 5 | Mode Projection Layer | Not Started | Only base mode listing/manifest endpoints exist; no advanced per-mode projection surfaces yet. |
| 6A | Player Identity Foundation | Deferred | The prototype `POST /v1/players/{puuid}/sync` route has been removed from the stable API. Next work should start with Riot account/PUUID/summoner persistence, job orchestration, and a DB-backed read contract. |
| 6B | Match Ingestion Foundation | Deferred | The early Riot match fetch/transform prototype files have been removed. Next work should start with durable cursoring, a match registry, stored payload/snapshot model, and ingestion job lifecycle. |
| 7 | Player Match Normalization Authority | Not Started | No DB-backed normalized per-match champion/item/rune/spell snapshots are exposed for consumers yet. |
| 8 | Patch & Seasonal Lifecycle Automation | In Progress | Patch poller baseline is implemented. Patch discovery and manual sync smoke both appear healthy on `continuum-mini`, including successful job-run completion after the 2026-03-30 summary regression fix; the next meaningful check is better operational visibility. |
| 9 | Testing & Data Quality Gate | In Progress | The Mini workspace `pytest` baseline is green again (`11 passed, 1 warning`), and direct regression coverage now exists for static-ingestion result summarization. Local re-checks in this sandbox are green with `TMPDIR=/dev/shm`, and dedicated jobs-endpoint coverage is now present. |
| 10 | Hardening & Production Discipline | In Progress | Logging and the Mini deployment target are established, and host-local `/v1/health` plus `/v1/version` are green. Operational confidence still needs docs alignment, broader smoke coverage, and deployment/runtime verification notes to stay current. |
| 11 | Advanced Intelligence | Out of Scope for Core | Riot-core does not need an intelligence phase to serve as the data authority. Recommendation/classification/advice work should live in SoulRift or a separate intelligence service unless narrowed to factual data-quality enrichment. |

## Next Milestone Checklist

### Suggested Immediate Next Step

- [x] Reconcile roadmap status with the current repo branch/commit and implemented API surface.
- [x] Record the existing `/v1/jobs/recent`, `/v1/jobs/latest`, and `/v1/jobs/{job_id}` observability endpoints as part of the current authority surface.
- [x] Re-run the non-mode pytest slice locally with `TMPDIR=/dev/shm` and record the current result (`10 passed, 1 warning in 0.09s`).
- [x] Unstick `tests/test_modes_read.py` and `tests/test_mode_manifest.py` so the full local suite no longer hangs (rechecked on 2026-04-10).
- [x] Add dedicated tests for the jobs endpoints, including filter validation and response metadata expectations.
- [ ] Document the jobs endpoints in `docs/api.md` and note how they should be used for ingestion visibility.
- [ ] Normalize jobs endpoint error payloads so they follow the same `{code, message}` detail pattern used by the static and mode routes.
- [ ] Align jobs endpoint validation behavior across `/v1/jobs/recent` and `/v1/jobs/latest` so the observability contract is consistent.

### Phase 1 Kickoff (Riot Access & Compliance)

- [x] Add shared outbound HTTP client with retry + backoff + jitter + timeout defaults
- [x] Route queue catalog and remaining outbound fetches through the shared client
- [ ] Define Riot rate-limit budget and per-endpoint call strategy
- [ ] Add region/platform routing policy (`americas`, `asia`, `europe`, platform shards)
- [ ] Enforce secret hygiene (`RIOT_API_KEY` env-only, log redaction, no key echo in errors)
- [x] Expose recent/latest/by-id ingestion job outcomes through `/v1/jobs/*`
- [ ] Add basic ingestion telemetry counters (success/failure/retry/ratelimited)
- [x] Re-verify the current shared HTTP client implementation in code

### Phase 2 Closure (Patch & Static Data Authority)

- [x] DDragon patch sync endpoint
- [x] Static ingestion for champion/item/runes/summoner
- [x] Asset hash + metadata persistence
- [x] Read endpoints (`/v1/patch`, `/v1/champions`, `/v1/items`, `/v1/runes`, `/v1/summoners`)
- [x] Add scheduler/poller for automatic patch checks and ingestion
- [x] Fix the current static-ingestion regression introduced during the shared HTTP refactor
- [x] Ensure failed asset downloads fail the sync job/poller outcome instead of being reported as success
- [x] Repair the `ddragon` route import/response-helper regression so sync endpoints load again
- [x] Expose recent/latest/by-id sync job status from `job_run_registry`
- [ ] Add ingestion status tracking/telemetry for background task outcomes
- [x] Re-verify background sync end-to-end on `continuum-mini` after the current docs/verification refresh
- [ ] Add broader direct tests for static ingestion and sync failure paths beyond the current summary regression coverage
- [ ] Add docs and endpoint tests for `/v1/jobs/*`

### Phase 3 Stabilization (Mode Authority Core)

- [x] Migration for `mode_registry`, `mode_patch_registry`, `mode_queue_binding`
- [x] SQLAlchemy mode models (`app/models/mode.py`) with mapper configuration verified
- [x] Mode discovery endpoint: `GET /v1/modes`
- [x] Mode manifest endpoint: `GET /v1/modes/{mode_key}/manifest`
- [x] Validate `alembic upgrade head` against live Mini/local Postgres and record the current Mini outcome in docs
- [x] Add queue-to-mode ingest/bootstrap workflow
- [x] Add tests for mode read paths and failure cases (`tests/test_modes_read.py`, `tests/test_mode_manifest.py`)
- [x] Make the default project test harness pass again after the shared app import regression is fixed
- [x] Resolve the remaining local hang in `tests/test_modes_read.py` and `tests/test_mode_manifest.py`

### Phase 4 Kickoff (Consumer Integration Contracts)

- [ ] Define versioned API contract policy (`/v1` compatibility and breaking-change rules)
- [ ] Standardize envelope for errors/pagination/metadata across read endpoints
- [x] Add an initial paginated list surface with validation metadata on `/v1/jobs/recent`
- [ ] Define canonical filters/sort/pagination semantics for list endpoints
- [ ] Publish first contract doc for consumers (`modes`, `patch`, `player matches`, `jobs`)

### Phase 6A Kickoff (Player Identity Foundation)

- [ ] Add core entities: `riot_account`, `summoner_profile`
- [x] Remove the current prototype `POST /v1/players/{puuid}/sync` from the stable `/v1` API
- [ ] Add the future authority-shaped `POST /v1/players/{puuid}/sync` only when it schedules ingestion and returns DB-backed job/readiness state
- [ ] Add identity sync logic for account + summoner profile refresh

### Phase 6B Kickoff (Match Ingestion Foundation)

- [ ] Add core entities: `player_match_registry`, ingest cursor/state
- [ ] Add read endpoint: `GET /v1/players/{puuid}/matches`
- [ ] Persist extracted per-match snapshots (mode queue, champion, item build, runes, summoner spells)
- [ ] Move recommendation/build-classification logic out of riot-core or explicitly defer it to a separate intelligence surface

### Phase 9 Gate (Testing & Data Quality)

- [ ] Migration replay tests from zero-state to head on ephemeral Postgres
- [x] Re-run the current project `pytest` suite in a writable Mini dev environment and record the baseline
- [x] Re-run the local non-mode pytest slice with `TMPDIR=/dev/shm` and record the current result
- [x] Add retry/error-path tests for the shared HTTP client
- [x] Resolve the local timeout/hang in `tests/test_modes_read.py` and `tests/test_mode_manifest.py`
- [x] Add endpoint tests for `/v1/jobs/recent`, `/v1/jobs/latest`, and `/v1/jobs/{job_id}`
- [ ] Contract tests for static/mode/player endpoints
- [ ] Idempotency tests for patch and player sync flows
- [ ] Fixture replay tests using stored Riot payload samples
- [x] Replace the stale failure narrative with the current Mini verification baseline in docs/roadmap
- [x] Add direct regression coverage for the `ddragon_sync` summary-path failure that previously flipped successful runs to `failed`

## Git Workflow Guardrails (Solo Professional Baseline)

Use this workflow for every roadmap item unless explicitly overridden:

- [ ] Create work only on topic branches (`feature/*`, `fix/*`, `chore/*`, `docs/*`); do not commit directly to `main`.
- [ ] Keep branch scope aligned to one roadmap unit (single phase milestone or one tightly-coupled slice).
- [ ] Rebase or merge `main` into branch before opening/finalizing PR to reduce drift and migration surprises.
- [ ] Open a PR for every branch, even when self-merging, with: purpose, verification commands, and deferred follow-ups.
- [ ] Require passing CI checks before merge (tests/lint/migrations when configured).
- [ ] Prefer squash merge for feature/fix branches to keep `main` history concise and readable.
- [ ] Delete merged branches immediately after merge.
- [ ] Tag significant milestones on `main` (`v0.x.y`) to preserve release checkpoints.
- [ ] If scope changes mid-branch, cut a new branch and move unrelated work there.

Recommended branch naming examples:

- `feature/mode-read-tests`
- `fix/alembic-offline-sql`
- `chore/patch-poller-baseline`
- `docs/api-contract-v1`

PR template checklist (copy into PR description):

```md
## Summary
- Phase / roadmap item:
- Scope (what this PR changes):
- Out of scope / deferred:

## Verification
- [ ] `alembic upgrade head` (or N/A with reason)
- [ ] Tests run and pass (list commands)
- [ ] Manual smoke checks completed (list endpoints/flows)

## Docs and Contract
- [ ] ROADMAP updated (if status changed)
- [ ] API/docs updated (if behavior changed)
- [ ] Breaking change? If yes, include migration/consumer notes

## Git Hygiene
- [ ] Branch name follows convention (`feature/*`, `fix/*`, `chore/*`, `docs/*`)
- [ ] PR scoped to one roadmap slice
- [ ] Follow-up issues linked for deferred work
```

## Immediate Build Order

1. Define the Phase 6A/6B storage model before reintroducing player/match API surface.
2. Document and test the existing `/v1/jobs/*` observability surface.
3. Normalize error/pagination semantics across endpoints and define the Phase 4 contract baseline.
4. Expand poller/ingestion observability beyond job history into counters, health visibility, and rate-limit surfacing.
5. Add broader sync-path tests around failure handling and idempotency.
6. Keep Mini deployment verification notes current when runtime fixes land outside the repo working tree.

## Recommended Next Step

The most logical immediate task is to define the DB-backed Phase 6A/6B player and match authority model before reintroducing player/match API surface.

Why this is next:

- The removed `POST /v1/players/{puuid}/sync` prototype fetched and returned live Riot match data, but riot-core should persist facts first and serve DB-backed query endpoints.
- The removed match/player transform files were useful exploration, but the consumer contract should come after `riot_account`, match registry, cursoring, and stored snapshots exist.
- Build classification and recommendation logic is better kept in SoulRift or a separate intelligence surface, not in the core authority path.

Execution focus:

1. Define the Phase 6A/6B persistence model: `riot_account`, `summoner_profile`, `player_match_registry`, ingest cursor/state, raw match payload storage or references, and normalized match snapshots.
2. Define the future `POST /v1/players/{puuid}/sync` and `GET /v1/players/{puuid}/matches` contracts around jobs and DB-backed reads.
3. Keep `/v1/jobs/*` docs/error cleanup next in line, because job visibility will be needed by the eventual player/match sync path.
4. Refresh verification notes after the stable app import/test baseline is re-run.

## Direction

Near-term direction for the project:

1. Reconcile docs, roadmap, and test verification notes so the repo tells one consistent story.
2. Make the full pytest baseline consistent across local and Mini environments.
3. Finish the current job-observability slice with tests, docs, and consistent errors.
4. Add deeper observability around ingestion and patch polling.
5. Validate deployment/migration posture and capture it in docs.
6. Freeze consumer-facing contracts before starting player identity and match ingestion work.

What not to do yet:

- Do not start player ingest or match-history authority work before the static/sync and jobs-observability baselines are verifiably stable.
- Do not reintroduce player/match endpoints as a consumer contract until persistence, job status, and DB-backed read endpoints exist.
- Do not add build recommendation or classification logic to riot-core's core service path.
- Do not treat docs as authoritative until the jobs endpoints and response-shape verification notes are refreshed to match current code.

## Project Tree (Current)

```text
continuum-riot-core/
├─ AGENTS.md
├─ .env.example
├─ .gitignore
├─ README.md
├─ ROADMAP.md
├─ pyproject.toml
├─ alembic.ini
├─ alembic/
│  ├─ env.py
│  ├─ script.py.mako
│  └─ versions/
│     ├─ a6673c90b13c_add_patch_registry.py
│     ├─ 24b217004927_add_asset_registry.py
│     ├─ 6d7f9db2b6b1_fix_patch_registry_discovered_at_column.py
│     ├─ 76cb22759f36_add_mode_registry_tables.py
│     └─ a80417ec8616_add_job_run_registry_table.py
├─ app/
│  ├─ main.py
│  ├─ api/
│  │  ├─ contract.py
│  │  ├─ pagination.py
│  │  ├─ response.py
│  │  ├─ router.py
│  │  └─ v1/
│  │     ├─ ddragon.py
│  │     ├─ health.py
│  │     ├─ jobs.py
│  │     ├─ modes.py
│  │     ├─ static.py
│  │     └─ version.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ logging.py
│  │  ├─ paths.py
│  │  └─ types.py
│  ├─ db/
│  │  ├─ engine.py
│  │  └─ session.py
│  ├─ models/
│  │  ├─ asset.py
│  │  ├─ base.py
│  │  ├─ job_run.py
│  │  ├─ mode.py
│  │  └─ patch.py
│  ├─ services/
│  │  ├─ ddragon.py
│  │  ├─ http_client.py
│  │  ├─ job_registry.py
│  │  ├─ mode_authority.py
│  │  ├─ mode_classifier.py
│  │  ├─ mode_read.py
│  │  ├─ mode_seed.py
│  │  ├─ patch_poller.py
│  │  ├─ queue_catalog.py
│  │  ├─ static_ingestion.py
│  │  └─ static_read.py
│  └─ utils/
│     └─ hash.py
├─ docs/
│  ├─ README.md
│  ├─ api.md
│  ├─ architecture.md
│  └─ development.md
├─ infra/
│  └─ postgres/
│     └─ compose.yaml
└─ tests/
   ├─ conftest.py
   ├─ test_contract.py
   ├─ test_http_client.py
   ├─ test_jobs.py
   ├─ test_mode_classifier.py
   ├─ test_mode_manifest.py
   ├─ test_modes_read.py
   └─ test_static_ingestion.py
```

## Recommended Agent Context

When starting a new ChatGPT/Codex session, provide these files first so the assistant can reason accurately without rediscovering repo structure.

Always include:

- `AGENTS.md`
- `ROADMAP.md`
- `pyproject.toml`
- `.env.example`
- `app/core/config.py`
- `app/main.py`
- `app/api/router.py`

Include for the current shared HTTP + sync phase:

- `app/services/http_client.py`
- `app/services/ddragon.py`
- `app/services/static_ingestion.py`
- `app/services/queue_catalog.py`
- `app/services/patch_poller.py`
- `app/api/v1/ddragon.py`
- `app/api/v1/jobs.py`
- `app/services/job_registry.py`
- `tests/conftest.py`
- `tests/test_http_client.py`
- `tests/test_static_ingestion.py`

Include when DB behavior or migrations are in scope:

- `app/db/session.py`
- `app/db/engine.py`
- `app/models/asset.py`
- `app/models/patch.py`
- `app/models/job_run.py`
- latest files in `alembic/versions/`

Include when mode authority work is in scope:

- `app/services/mode_authority.py`
- `app/services/mode_seed.py`
- `app/services/mode_classifier.py`
- `app/services/mode_read.py`
- `app/models/mode.py`
- `app/api/v1/modes.py`
- `tests/test_mode_classifier.py`
- `tests/test_modes_read.py`
- `tests/test_mode_manifest.py`

If a future phase changes focus, update this section along with the roadmap phase status so new sessions inherit the right context quickly.

## Open Risks

- Docs and roadmap now reflect the current Mini response shape and verification baseline, but `docs/api.md` still needs a follow-up pass for the jobs endpoints and any error-shape cleanup.
- `docs/architecture.md` still has stale player/match and test-hang wording; update it after the prototype quarantine decision is made.
- `continuum-mini` is still the deployment target, and `/v1/health`, `/v1/version`, and `POST /v1/ddragon/sync` are green.
- Live DB migration validation is not freshly re-confirmed in this session.
- This session produced a fresh local `pytest` baseline: `TMPDIR=/dev/shm .venv/bin/pytest -vv` reports `35 passed, 1 warning in 0.31s`.
- Locale drift risk exists when ingestion is triggered with a non-default locale while read paths are pinned to `DEFAULT_LOCALE`.
- Riot rate-limit policy, secret redaction guarantees, and regional routing contracts are still not defined.
- Contract drift risk remains high until pagination/error/versioning behavior is formally frozen.
