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

## Current Known Issues (2026-03-29)

- `app/services/static_ingestion.py` now uses positional log arguments on the ingestion path; the remaining branch-closure work is verification rather than this specific code cleanup.
- `tests/test_modes_read.py` and `tests/test_mode_manifest.py` remain unresolved until they are re-run in a normal writable dev environment.
- `pytest` could not be re-run from this sandbox because Python could not find a usable temporary directory (`FileNotFoundError` for `/tmp`, `/var/tmp`, `/usr/tmp`, and the repo root).
- `alembic upgrade head --sql` succeeded historically, but `alembic upgrade head` still needs fresh validation against healthy Postgres.
- `continuum-mini` was directly re-verified on 2026-03-29: `continuum-riot-core.service` is active and `GET /v1/health` succeeds on port `8000`.

## Troubleshooting

- Verify Postgres container health:
  - `docker compose -f infra/postgres/compose.yaml ps`
- Validate DB credentials/host in `.env`.
- Confirm `DATABASE_URL` uses `postgresql+asyncpg://` and `DATABASE_URL_SYNC` uses `postgresql+psycopg://`.
- If endpoints return `NO_CURRENT_PATCH`, run:
  - `POST /v1/ddragon/sync`
- If static endpoints return `ASSET_NOT_READY`, wait for background ingestion to finish and retry.
- Mini deployment checks:
  - `systemctl status continuum-riot-core.service --no-pager -l`
  - `journalctl -u continuum-riot-core.service -n 100 --no-pager`
  - `curl http://127.0.0.1:8000/v1/health`
  - `curl http://192.168.0.74:8000/v1/health`
