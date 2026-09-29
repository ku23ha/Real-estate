# Rethos implementation plan

## Product journey

```text
Deal → Property → 10–20 synthetic/authorized comps → Comparable Engine
→ Valuation → Finance → Maximum Acquisition Price → Scenario → Memo
```

The first release is a modular monolith. Every calculation consumes explicit, versioned inputs; every material evidence value carries provenance. Synthetic fixtures are labeled as synthetic. External data is accepted only when its source and usage permission are recorded. No connector is enabled by virtue of public visibility alone.

## Architecture

- `apps/web`: Next.js, TypeScript, Tailwind and shadcn/ui; presentation and typed API client only.
- `apps/api`: FastAPI + Pydantic; domain/API orchestration, persistence and validation.
- `packages/financial-engine`: pure deterministic finance functions and versioned calculation outputs.
- `packages/context-engine`, `evidence-engine`, `comparable-engine`, `scenario-engine`: independent domain modules.
- PostgreSQL is the initial system of record. PostGIS is reserved for later location queries; object storage is for uploaded documents and immutable source snapshots.
- LLM provider abstraction may extract or explain structured data, but cannot calculate financial outputs or choose authoritative values.

## Vertical slices

1. Create Deal → store Property → display Deal (implemented as the initial scaffold).
2. Import 10–20 synthetic/authorized comparables → validate, normalize and retain provenance.
3. Apply hard filters, rank eligible comps and explain matches/differences.
4. Produce an indicative valuation and range.
5. Add rent and deterministic financial underwriting.
6. Solve maximum acquisition price with explicit solver statuses.
7. Recalculate immutable base assumptions with scenario overrides.
8. Compile evidence context, generate an evidence-backed memo and support human review.

## Initial slice acceptance

- A deal has one associated property record and can be created, retrieved and listed.
- Inputs are typed and validated; IDs are generated server-side.
- API errors are explicit; no fake persistence or fabricated market data is presented as real.
- UI makes the Deal → Property relationship visible and labels the implementation as an early scaffold.

## Open decisions

- **OPEN DECISION — BLOCKED UNTIL FOUNDER CONFIRMS:** initial launch geography and canonical area/currency conventions.
- **OPEN DECISION — BLOCKED UNTIL FOUNDER CONFIRMS:** production database provider, authentication/organization tenancy and deployment target.
- **OPEN DATA / LEGAL REVIEW — BLOCKED:** no production connector until commercial use, storage, attribution and redistribution terms are documented.
- **OPEN DECISION — BLOCKED UNTIL FOUNDER CONFIRMS:** business-specific valuation adjustments, rent assumptions and acquisition solver conventions.

The scaffold deliberately avoids deciding these business rules.
