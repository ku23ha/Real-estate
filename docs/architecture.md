# Rethos architecture

## Current implementation

The repository is a two-app starter, not yet the complete modular monolith described in the handoff.

```text
Browser
  └─ apps/web: Next.js App Router page
       └─ HTTP → apps/api: FastAPI + Pydantic
                    └─ SQLAlchemy session → PostgreSQL
                           ├─ deals
                           └─ properties
```

The page submits one Deal and nested Property object, then requests the deal list. The API owns validation and generated IDs. It connects to the database named by `DATABASE_URL`; `postgres://` and `postgresql://` URLs are normalized to the declared Psycopg 3 driver. Database tables are managed through Alembic, not created implicitly at API startup. CORS currently allows the local web origin. There is no authentication or full domain package boundary.

## Intended architecture from handoff

```text
Next.js UI → FastAPI API → SQLAlchemy persistence
                           └─ PostgreSQL
                                  └─ deals / properties
```

Planned domain services:

```text
Next.js UI → FastAPI API → domain services
                           ├─ Deal / Property
                           ├─ Evidence / Comparable / Context
                           ├─ Valuation / Rent
                           ├─ Deterministic Financial Engine
                           ├─ Scenario / Sensitivity
                           └─ Memo / Human Decision
                                  ↓
                        PostgreSQL
```

Keep a modular monolith. PostgreSQL is the persistent system of record for Deal/Property in M1. Add PostGIS only when spatial requirements are approved and implemented. Add object storage only with document/source snapshot requirements. No connectors, external datasets, distributed infrastructure, or LLM integration were added in RET-003.

## Component responsibilities

- **Web:** present the deal workflow and collect user inputs; no financial calculations or source selection rules.
- **API:** typed boundary validation, authorization (when designed), orchestration, persistence, and stable errors.
- **Evidence/comparable/context modules:** retain permission/provenance and determine which evidence qualifies for a calculation.
- **Valuation/rent/finance/scenario modules:** deterministic, versioned calculations from explicit snapshots. An LLM is never authoritative for numeric results.
- **Memo/review:** render supported outputs with source/model references and capture human changes and decisions.

Evidence, comparable, context, valuation, rent, finance, scenario, and memo modules remain planned, not present. Introduce them with the milestone that needs them rather than creating empty package shells.

## Schema lifecycle

- `DATABASE_URL` is required to start the API and run migrations.
- Alembic migration `20260930_0001` creates `deals` and `properties`; `alembic downgrade base` reverses it and drops their data.
- The property foreign key is unique, preserving one Property per Deal. Area pair/positive constraints duplicate existing API validation at the database boundary.
- Primary keys and the unique foreign-key constraint are the only indexes.
- SQLite is used for isolated automated tests and a local smoke check only. Documented application setup targets PostgreSQL.
- `app.seed` can insert one idempotent synthetic Deal/Property fixture; it does not represent market evidence.

## Data and reproducibility invariants

- Preserve raw observations and provenance; do not silently replace history.
- Clearly label fixtures as synthetic or authorized.
- Treat source permission as an enforced input to evidence selection; unknown/prohibited sources are excluded.
- Version material calculations and retain input/data/assumption snapshots so the same snapshots and model version reproduce results.
- Keep the base assumption set immutable when running scenarios.
- Abstain or request review when evidence is insufficient or material inputs conflict.
- Do not infer geography, canonical area/currency conventions, finance formulas or valuation adjustments.

## Dependency-ordered delivery

M0 baseline → M1 persistent Deal/Property → M2 evidence/comparables → M3 valuation/rent → M4 deterministic finance → M5 maximum price → M6 scenario/sensitivity → M7 context → M8 memo/human decision. Detailed gates and the next ticket are in [current-state.md](current-state.md). M9 Document AI and M10 an external connector are beyond this request and must follow M8 plus separate approval/source review.
