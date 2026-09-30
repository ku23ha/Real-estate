# RET-020 — Evidence and Provenance

## Scope delivered

- Persist descriptive evidence-source records and Deal-scoped evidence observations.
- Retain the supplied raw JSON, optional normalized JSON, and required provenance JSON separately.
- Record source type, reference, and rights status/notes as supplied. These fields do not certify that data may be used.
- Provide create/list/get API operations. The API provides no update or delete operation for evidence observations.
- Add reversible migration `20260930_0003` after the RET-010 schema.
- No source connectors, evidence ranking, comparable import, valuation, or calculations are included.

## API

- `POST/GET /api/v1/evidence-sources`; `GET /api/v1/evidence-sources/{source_id}`
- `POST/GET /api/v1/deals/{deal_id}/evidence`; `GET /api/v1/deals/{deal_id}/evidence/{evidence_id}`

Evidence creation requires an existing Deal, an existing source record, raw content, and provenance. Normalized content and observed time are optional. The service records rights metadata without interpreting its legal effect.

## Open decisions and limits

- **OPEN DATA / LEGAL REVIEW — BLOCKED:** accepted rights-status vocabulary and the conditions under which a source/evidence record is usable downstream.
- Authentication, organization tenancy, access control, retention, and audit actors remain unresolved under RET-010 decisions. These endpoints must not be treated as production authorization boundaries.
- Raw and provenance JSON have no ticket-specific content schema yet; this ticket preserves input without assigning real-estate meaning or normalizing it.
- PostgreSQL/RDS host verification remains pending under RET-003. Local migration verification uses SQLite.

## Verification

See the RET-020 completion report for the test and migration commands/results. Run `alembic upgrade head` with the configured database before using the API.
