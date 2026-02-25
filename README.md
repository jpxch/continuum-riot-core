# continuum-riot-core

`continuum-riot-core` is the backend data authority service for Riot-powered consumers (including your LoL companion app).

## Current Direction

This project is heading in the correct direction for an always-on server, but it is not fully there yet.

Implemented today:
- FastAPI service with versioned routes under `/v1`
- Health/version endpoints
- DDragon patch sync trigger: `POST /v1/ddragon/sync`
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

## What Is Not Finished Yet

The service still needs core pieces before it can be treated as fully always-on production authority:
- Automated periodic sync/poller (currently sync is request-triggered)
- Full Riot player/match ingestion pipeline
- Mode authority stabilization (`mode_registry` model/mapping cleanup + validation)
- Contract and pagination/error policy hardening for downstream clients
- Test suite and migration replay coverage
- Operational hardening (monitoring, alerting, SLOs)

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
   - `alembic upgrade head`
4. Start API:
   - `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Source of Truth

Roadmap and phase tracking live in `ROADMAP.md`.  
This README summarizes current implementation status without changing roadmap structure.
