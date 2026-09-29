# Initial implementation tickets

## Ticket status

- **RET-001 — BLOCKED:** Git metadata exists, but the environment denies writes to `.git/index.lock` and `.git/config`, including after a scoped write request. No local baseline commit or remote was created. The previously corrected public target `https://github.com/ku23ha/Real-estate-pro` currently contains a README-only commit, not the audited source baseline. The handoff also names `https://github.com/ku23ha/Real-estate`; confirm which repository is authoritative before configuring a remote.
- **RET-003 — ACTIVE:** PostgreSQL URL configuration, SQLAlchemy persistence, initial Alembic migration, seed fixture and persistence tests are implemented. Latest local suite: 10 passed, 1 skipped (PostgreSQL integration). The required AWS CLI checks are blocked because `aws` is not installed/recognized; previous console checks also showed account setup/free-plan limitations. No AWS identity was verified and no AWS resources were created. Do not mark complete until real PostgreSQL verification succeeds.
- **RET-010 — NEXT:** Deal + Property stable. Do not start until RET-003's PostgreSQL integration check is complete.

## Foundation

- RET-002 Add frontend and backend local entry points and environment examples.
- RET-003 Add PostgreSQL `DATABASE_URL` configuration, migration framework and initial deal/property migration.
- RET-004 Add CI, structured logging and error reporting configuration.
- RET-005 Establish source registry fields and block unknown/prohibited sources.

## Domain and first slice

- RET-010 Define Deal and Property schemas and validation.
- RET-011 Create and list deals with attached property.
- RET-012 Build deal list/create UI and deal detail view.
- RET-013 Persistence and initial migration scope is covered by RET-003.

## Evidence through decision memo

- RET-020 Evidence/source/provenance schemas and quality labels.
- RET-030 Import 10–20 synthetic or authorized comps; validate units, dates, price and permission metadata.
- RET-031 Comparable hard filters, normalization, transparent ranking and explanations.
- RET-040 Deterministic indicative valuation, range, limitations and model version.
- RET-041 Rent evidence and supported yield calculations.
- RET-042 Cash flow, IRR, NPV, ROI, MOIC and profit pure functions.
- RET-050 Maximum acquisition price solver and required result statuses.
- RET-060 Immutable scenario base plus validated overrides and sensitivity.
- RET-070 Evidence context compilation, exclusions, deduplication and abstention.
- RET-080 Evidence-backed memo, provenance and human review/decision capture.
- RET-090 One-geography connectors only after source safety review is complete.

## Acceptance discipline

Each engine slice adds deterministic unit tests and golden/negative cases. Connector work includes source terms and provenance. No accuracy claims before validation against appropriate independent data.

## User-directed sequence after RET-010

RET-020 Evidence + Provenance → RET-030 Comparable import → RET-031 Comparable ranking → RET-040 Valuation → RET-043 Cash flow → RET-044 IRR → RET-045 NPV → RET-050 Maximum Acquisition Price. After the deterministic pipeline, proceed to scenario/report work, then introduce the Context Engine. External data connectors remain out of scope until separately approved and source rights are reviewed.
