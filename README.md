# continuum-riot-core

`continuum-riot-core` is the backend data authority service for Riot-powered consumers (including your LoL companion app).

Primary runtime target: `continuum-mini` (`192.168.0.74`).

## Current Direction

This project is heading in the correct direction for an always-on server, but it is not fully there yet.

Implemented today:
- FastAPI service with versioned routes under `/v1`
- Health/version endpoints
- DDragon patch sync trigger: `POST /v1/ddragon/sync`
- Patch poller baseline started from app lifespan
- Static asset ingestion + persistence for:
  - champions
  - items
  - runes
  - summoner spells
- Read endpoints:
  - `GET /v1/patch`
  - `GET /v1/champions`
  - `GET /v1/items`
  - `GET /v1/runes`
  - `GET /v1/summoners`
  - `GET /v1/modes`
  - `GET /v1/modes/{mode_key}/manifest`
- Mode bootstrap/discovery write workflow
- Job-run tracking for background sync work
- Managed Mini deployment via `continuum-riot-core.service`

## What Is Not Finished Yet

The service still needs core pieces before it can be treated as fully always-on production authority:
- Stronger ingestion telemetry/observability around the current poller baseline
- Full Riot player/match ingestion pipeline
- Live DB migration validation (`alembic upgrade head`)
- Contract and pagination/error policy hardening for downstream clients
- Test suite and migration replay coverage
- Operational hardening (monitoring, alerting, SLOs)

Current verified blockers as of 2026-03-29:
- `continuum-mini` was directly re-verified on 2026-03-29: `continuum-riot-core.service` is active and host-local `GET /v1/health` plus `GET /v1/version` return `200` on port `8000`
- The `ddragon` response-helper typo is fixed and Mini host import verification succeeds with `/opt/continuum-riot-core/.venv/bin/python -c "import app.main"`
- `pytest` is green in the Mini workspace on 2026-03-29: `11 passed, 1 warning in 0.24s`
- `alembic upgrade head` is green on `continuum-mini` on 2026-03-29 and completes without error against Postgres
- `POST /v1/ddragon/sync` smoke verification is green on `continuum-mini`: it returns the success envelope, reports patch `16.6.1`, and is followed by a `Mode authority sync complete` log entry
- The main remaining runtime/documentation gaps are richer ingestion telemetry and consumer contract hardening

## Project Scope

This server is intended to own:
- ingestion from Riot/DDragon
- normalization and storage
- read APIs for downstream apps

It is not the consumer app itself.

## Quick Start

1. Configure environment:
   - copy `.env.example` to `.env`
   - set `DATABASE_URL`, `DATABASE_URL_SYNC`, and `RIOT_API_KEY`
2. Start Postgres (optional local compose):
   - `docker compose -f infra/postgres/compose.yaml up -d`
3. Run migrations:
   - `.venv/bin/alembic upgrade head`
4. Start API:
   - `.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Mini Deployment

- Managed runtime on `continuum-mini` uses a systemd unit: `continuum-riot-core.service`
- Deployed app path on Mini: `/opt/continuum-riot-core`
- Service env file on Mini: `/etc/continuum-riot-core.env`
- Expected LAN endpoint: `http://192.168.0.74:8000`

## Documentation

- [docs/README.md](docs/README.md) - docs index
- [docs/architecture.md](docs/architecture.md) - system architecture and data flow
- [docs/api.md](docs/api.md) - API endpoint behavior and response shapes
- [docs/development.md](docs/development.md) - local development, verification, and troubleshooting

## Source of Truth

Roadmap and phase tracking live in `ROADMAP.md`.  
This README summarizes current implementation status without changing roadmap structure.
