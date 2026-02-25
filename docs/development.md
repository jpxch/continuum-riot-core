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
   - `. .venv/bin/activate && alembic upgrade head`
5. Run API:
   - `. .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Useful Commands

- Import check:
  - `. .venv/bin/activate && python -c "import app.main"`
- Compile check:
  - `. .venv/bin/activate && python -m compileall -q app alembic`
- Alembic head:
  - `. .venv/bin/activate && alembic heads`
- Alembic history:
  - `. .venv/bin/activate && alembic history`
- Test run:
  - `. .venv/bin/activate && pytest -q`

## Current Known Issues (2026-02-25)

- `pytest -q` exits code 5 because no tests are discovered in configured `tests` path.
- `alembic upgrade head --sql` fails due runtime schema inspection in migration `6d7f9db2b6b1`.
- `alembic upgrade head` requires healthy local DB connectivity; if Postgres is unavailable or DSN is wrong it fails with `OperationalError`.

## Troubleshooting

- Verify Postgres container health:
  - `docker compose -f infra/postgres/compose.yaml ps`
- Validate DB credentials/host in `.env`.
- Confirm `DATABASE_URL` uses `postgresql+asyncpg://` and `DATABASE_URL_SYNC` uses `postgresql+psycopg://`.
- If endpoints return `NO_CURRENT_PATCH`, run:
  - `POST /v1/ddragon/sync`
- If static endpoints return `ASSET_NOT_READY`, wait for background ingestion to finish and retry.
