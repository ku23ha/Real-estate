# Rethos MVP execution plan

## North star

Deliver one demonstrable deal workflow whose analytical outputs can be reproduced and traced to evidence and assumptions. Build one tested vertical slice at a time. This plan does not authorize external data connections or production deployment.

## Current foundation

- RET-010 is committed at `418a316`.
- RET-020 is committed at `80b6432`.
- RET-003 application/database code exists; host-side RDS PostgreSQL migration, integration, and restart verification remains pending.
- The API is a FastAPI modular monolith using SQLAlchemy and Alembic. The existing Next.js application is a minimal Deal create/list scaffold.
- Source-rights records are metadata supplied by the operator; they are not independently verified.

## First Golden Deal slice implemented

The API now supports manually linking a comparable to existing Deal evidence, importing comparable rows from CSV with a source and per-row raw evidence/provenance, listing comparables, and requesting an indicative value for a Deal.

The reproducible synthetic fixture is seeded locally with:

- One synthetic residential apartment property in `Synthetic Market A`, with an area of 1,000 `sqft`.
- Five synthetic transaction observations dated April through August 2026, recorded in `INR` and `sqft`.
- Each comparable linked to its raw Evidence record and a source marked `synthetic`.
- Run after migrations with `python -m app.golden_deal`; repeated runs are idempotent.

Comparable unit rate is `reported_price / reported_area`, rounded to four decimal places. The experimental indicative estimate requires exact case-insensitive match on location label, property type, area-unit label, and currency code; excludes future-dated and non-approved rights-status values; uses the median unit rate for the center and observed minimum/maximum rates for the range. The result exposes matched evidence-linked comparable IDs and excluded counts. It performs no location inference, fuzzy matching, adjustments, area conversion, FX conversion, source-quality weighting, or confidence claim.

The Golden Deal fixture returns an indicative range of INR 9,500,000–11,000,000, with an INR 10,000,000 center. These are synthetic demonstration figures, not market observations or an approved valuation method.

## Remaining phased plan

### Phase 1 — Comparable workflow

- Complete comparable import error reporting, deduplication behavior, and explicit data-quality/ranking explanation.
- Add frontend flow for manual/CSV input, evidence linkage, comparable review, and the indicative result.
- Keep the current median/min-max estimate explicitly provisional. **OPEN DECISION — BLOCKED UNTIL FOUNDER CONFIRMS:** approved valuation method, weighting, range construction, adjustments, and minimum evidence requirements.

### Phase 2 — Rental and project economics

- Add user-entered rent/operating assumptions and label them as assumptions, with evidence-linked rent records when provided.
- Add deterministic feasibility and period-based cash-flow calculations with explicit inputs, units, formulas, and tests.
- **OPEN DECISION — BLOCKED UNTIL FOUNDER CONFIRMS:** return conventions, cash-flow timing, taxes, debt, sale/exit, rent/vacancy/expense assumptions, construction cost semantics, and permitted area/FSI semantics.

### Phase 3 — Scenario and acquisition price

- Build independently calculated Base/Upside/Downside cases from an immutable base input set.
- Implement maximum-acquisition-price search only after target-return and cash-flow conventions are approved; expose solver status, assumptions, and reproducibility trace.
- Add golden regression assertions for scenario differences, edge cases, and acquisition-price reproducibility.

### Phase 4 — Context, quality, and memo

- Compile exact included/excluded evidence, comparables, calculations, assumptions, missing inputs, and provenance into a deterministic decision context.
- Generate a template-based memo from stored results, with human review and no automatic investment verdict.
- Add risk/data-quality measures only when their definitions are explicit and testable.

### Phase 5 — Product and deployment

- Complete the minimal Next.js workflow from Deal creation through evidence, comparables, assumptions, analysis, and memo.
- Run the complete Golden Deal through API and UI with deterministic local data.
- Finish RET-003 host PostgreSQL verification before using RDS for an MVP demo. Then document the smallest safe demo deployment path. No Kubernetes or external source connectors are in scope.

## API added in the first slice

- `POST/GET /api/v1/deals/{deal_id}/comparables`
- `POST /api/v1/deals/{deal_id}/comparables/import` (CSV)
- `POST /api/v1/deals/{deal_id}/valuation`

CSV headers: `transaction_date,reported_price,currency_code,property_type,area_value,area_unit,location_label`; optional headers: `project_name,developer_name`. Imported rows preserve their original text in Evidence `raw_content`, and each row receives an import provenance record.

## Verification

`apps/api/tests/test_comparables.py` exercises the Golden Deal valuation, evidence linkage, CSV import/raw preservation, malformed CSV, duplicate rejection, rights filtering, missing property, and deterministic repeated output. Migration `20260930_0004` is reversible and is included in migration upgrade/downgrade tests. PostgreSQL-backed verification still requires the host-side RET-003 runbook.
