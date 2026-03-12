# Development

## Local Setup

1. Create environment file:
   - `cp .env.example .env`
2. Ensure these values are set in `.env`:
   - `DATABASE_URL`
   - `DATABASE_URL_SYNC`
   - `RIOT_API_KEY`
3. Start local Postgres:
   - `docker compose -f infra/postgres/compose.yaml up -d`
4. Run migrations:
   - `.venv/bin/alembic upgrade head`
5. Run API:
   - `.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Useful Commands

- Import check:
  - `.venv/bin/python -c "import app.main"`
- Compile check:
  - `.venv/bin/python -m compileall -q app alembic`
- Alembic head:
  - `.venv/bin/alembic heads`
- Alembic history:
  - `.venv/bin/alembic history`
- Alembic offline SQL:
  - `.venv/bin/alembic upgrade head --sql`
- Test run:
  - `.venv/bin/pytest -q`
- Targeted classifier test:
  - `.venv/bin/pytest -q tests/test_mode_classifier.py`
- Targeted mode tests:
  - `.venv/bin/pytest -q tests/test_modes_read.py tests/test_mode_manifest.py`

## Current Known Issues (2026-03-12)

- `tests/test_mode_classifier.py` passes, but `tests/test_modes_read.py` and `tests/test_mode_manifest.py` currently hang in timeout-based verification.
- `alembic upgrade head --sql` now succeeds.
- `alembic upgrade head` requires healthy local DB connectivity; if Postgres is unavailable or DSN is wrong it fails with `OperationalError`.
- `continuum-mini` is reachable over SSH, but `curl http://127.0.0.1:8000/v1/health` currently fails with connection refusal.

## Troubleshooting

- Verify Postgres container health:
  - `docker compose -f infra/postgres/compose.yaml ps`
- Validate DB credentials/host in `.env`.
- Confirm `DATABASE_URL` uses `postgresql+asyncpg://` and `DATABASE_URL_SYNC` uses `postgresql+psycopg://`.
- If endpoints return `NO_CURRENT_PATCH`, run:
  - `POST /v1/ddragon/sync`
- If static endpoints return `ASSET_NOT_READY`, wait for background ingestion to finish and retry.
- If the Mini target appears up but port `8000` is refusing connections, verify the actual process binding and the launched app module on `continuum-mini`.
