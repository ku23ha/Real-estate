# Repository current state

Last updated: 2026-09-30 (RET-003 access verification). Clean-room implementation; no former-employer materials were used.

## Repository baseline

- Next.js/TypeScript frontend is in `apps/web`; FastAPI/Pydantic API is in `apps/api`.
- PostgreSQL is the target system of record. RET-003 adds SQLAlchemy persistence and Alembic migrations for Deal and Property.
- The repository's `.git` metadata is initialized, but the baseline files remain untracked and there is no commit. `git add` cannot create `.git/index.lock`, and adding `origin` cannot write `.git/config`, even after requesting `.git` write access; RET-001 therefore remains incomplete.
- No valuation, LLM, evidence, comparable, or external connector functionality was added in RET-003.

## Implemented

### API and persistence

- `DATABASE_URL` is required at API startup. Standard `postgres://` and `postgresql://` URLs are normalized to Psycopg 3; no credentials or database hostname are hard-coded.
- SQLAlchemy models persist `deals` and `properties` with UUID primary keys, timestamps, the one-property-per-deal FK, and the existing area validation represented as database constraints.
- Alembic migration `20260930_0001` creates these tables and supports downgrade to `base`.
- Existing Deal API paths and nested Property response shape are preserved: create, list, detail, and health.
- A repeatable, idempotent `python -m app.seed` inserts one clearly synthetic local fixture.
- `apps/api/.env.example` documents the expected URL format without secrets. The app reads environment variables directly; it does not implicitly load `.env` files.

### Verification

- Local API tests use temporary SQLite files so they run without a PostgreSQL service. The restart test closes one app instance, opens another against the same database file, and retrieves the saved Deal and Property.
- Latest run from `apps/api` using the existing ignored virtual environment and a workspace-local pytest temp directory: **10 passed, 1 skipped**. The skipped test is the PostgreSQL restart integration test because `TEST_DATABASE_URL` is unset. Plain `python -m pytest` cannot access the system temp directory in this environment; using `--basetemp ..\\..\\work\\pytest -p no:cacheprovider` resolves that sandbox limitation.
- Migration upgrade/downgrade, create, retrieve, list, Property persistence, restart persistence, synthetic seed idempotency, and DB health checks pass on SQLite.
- Uvicorn was started locally against a temporary SQLite smoke database; health, create, detail retrieval, and list returned expected results. The server was stopped after verification.
- No PostgreSQL server/client/container is available in this environment; PostgreSQL migration and connection behavior remain unverified here.
- Local `.venv` dependencies were installed from the declared API/dev requirements; `.venv` is gitignored.

## Remaining work and blockers

- Start/provision a disposable PostgreSQL database, set `TEST_DATABASE_URL`, and run the PostgreSQL integration test before calling RET-003 fully verified.
- RET-001 Git commit baseline remains blocked by restricted `.git` writes.
- AWS provisioning remains blocked. The required `aws sts get-caller-identity` and `aws configure list` checks cannot run because `aws` is not recognized in the current shell. Prior AWS Console checks routed RDS and CloudShell to **Complete your account setup / Free account plan access limitations**. No plan change, AWS identity verification, profile creation, or resource provisioning occurred. Do not provision until AWS CLI authentication works.
- `gh` is not installed, so `gh auth status` and `gh repo view` cannot run. In a previously authenticated browser session, `https://github.com/ku23ha/Real-estate-pro` was confirmed public and now contains a README-only commit; the rest of this local baseline was not uploaded. No force push or remote modification occurred.
- The requested URL in the handoff, `https://github.com/ku23ha/Real-estate`, differs from the previously corrected public target `https://github.com/ku23ha/Real-estate-pro`. No local remote has been configured; confirm which URL is authoritative before connecting it once Git metadata writes are available.
- Frontend runtime tooling is incomplete: Node is available, but `npm` is not recognized in the current shell. No dependencies were installed during this access check.
- No production auth, tenancy, deployment, CI, evidence/provenance, comparables, valuation, rent, finance, scenarios, Context Engine, memo, or external data connector is included.
- Business choices such as launch geography, area/currency conventions and financial methodology remain open; none are needed to implement the current Deal/Property schema.

## Ticket status and dependency order

- **RET-003 — ACTIVE; implementation and SQLite tests pass, awaiting authenticated AWS CLI access and PostgreSQL-backed verification.**
- Next requested milestone after RET-003 is **RET-010 — Deal + Property stable**. No RET-010 or later work was done in this task.
- The broader sequence remains RET-020 Evidence + Provenance → RET-030 Comparable import → RET-031 Comparable ranking → RET-040 Valuation → RET-043 Cash flow → RET-044 IRR → RET-045 NPV → RET-050 Maximum Acquisition Price, followed by the scenario/report workflow and then Context Engine only after the deterministic pipeline works.
