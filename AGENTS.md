# Rethos repository instructions

## Mission and boundaries

Build a clean-room real-estate underwriting and decision system. Work only from this repository, public generic engineering knowledge, licensed sources, authorized customer data, or independently generated synthetic fixtures. Never use former-employer material. Do not connect external data sources unless separately authorized and their rights are documented.

## Architecture

Use a modular monolith: Next.js/TypeScript UI in `apps/web`, FastAPI/Pydantic API in `apps/api`, and domain logic in independent packages as those are introduced. PostgreSQL is the planned system of record. Keep financial logic out of UI/routes; use deterministic engines for all numbers. Do not add infrastructure without a demonstrated need.

## Commands

After installing dependencies from the relevant manifest:

- API: from `apps/api`, set `DATABASE_URL`, run `alembic upgrade head`, then `uvicorn app.main:app --reload`.
- Local fixture: from `apps/api`, run `python -m app.seed` after migration.
- Web: from `apps/web`, run `npm run dev`.
- Python tests: from `apps/api`, run `python -m pytest`.
- PostgreSQL persistence integration: set `TEST_DATABASE_URL` to a dedicated disposable test database before running tests.
- Frontend checks: use scripts declared in `apps/web/package.json`; currently there is no test or lint script.

The current audit environment may not have Python, npm, or project dependencies installed. Report unavailable commands; do not silently install dependencies or bypass network restrictions.

## Coding and business invariants

- Keep API schemas typed and validate at boundaries.
- Same versioned inputs must yield reproducible calculations.
- LLMs may interpret, extract, or explain structured data; they are never financial authorities.
- Do not invent area/currency conventions, geography, valuation adjustments, finance definitions, or source rights. Record unresolved items as `OPEN DECISION — BLOCKED UNTIL FOUNDER CONFIRMS` or `OPEN DATA / LEGAL REVIEW — BLOCKED`.
- Preserve raw observations and provenance; label synthetic fixtures clearly.
- Do not overwrite a base assumption set when applying scenario overrides.

## Definition of done

For each approved ticket, add or update focused tests, run available tests and relevant app checks, update current-state/API documentation, and report changed files, verification, blockers, and next ticket. Stop when a business, data-rights, or security decision is unresolved. Do not proceed beyond the requested milestone.
