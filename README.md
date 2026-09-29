# Rethos clean-room scaffold

The API persists Deal and Property records and exposes the RET-010 reference domain entities. See [database schema and migrations](docs/database-schema.md), [domain model and open decisions](docs/domain-model.md), [architecture](docs/architecture.md), and [current state](docs/current-state.md).

## API local setup

Use Python 3.10+ and a PostgreSQL database created for local development. No database server is bundled with this repository.

```powershell
cd apps/api
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Set `DATABASE_URL` in the shell to the URL of that local database. For example, copy the placeholder format from `apps/api/.env.example` and replace every placeholder; the API does not load `.env` files automatically.

```powershell
$env:DATABASE_URL = "postgresql+psycopg://<user>:<password>@<host>:5432/<database>"
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

The seed creates only a synthetic local development fixture. API startup fails clearly when `DATABASE_URL` is unset. Existing Deal/Property routes remain unchanged. RET-010 adds create/list/retrieve routes for `/api/v1/organizations`, `/users`, `/developers`, `/projects`, `/locations`, and `/micro-markets` (under the `/api/v1` prefix).

To remove the initial schema, run `alembic downgrade base` from `apps/api`. This drops the Deal/Property tables and their data.

## Tests

```powershell
cd apps/api
python -m pytest
```

Tests use temporary SQLite databases for isolated API, migration rollback, and restart-persistence checks. To additionally run the PostgreSQL restart integration test, set `TEST_DATABASE_URL` to a dedicated disposable PostgreSQL test database; migrations and test records will be written to it.

## Web

```powershell
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000`. Set `NEXT_PUBLIC_RETHOS_API_URL` if the API is hosted elsewhere. Do not enter sensitive customer information into this scaffold.
