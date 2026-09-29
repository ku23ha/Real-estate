# Decision register

This file is the index for architecture and product decisions. A requirement explicitly stated in the Rethos handoff/master prompt is treated as a constraint; it is not silently converted into additional product behavior. No former-employer materials were used.

## Confirmed constraints

- Start with a modular monolith.
- Current declared stack: Next.js/TypeScript UI and FastAPI/Pydantic API.
- PostgreSQL is the planned database for persistent Deal/Property work.
- Financial outputs must come from deterministic, reproducible calculations; an LLM is not their authority.
- External data connectors remain disabled until source rights and operational terms are documented and approved.
- First comparable set is limited to 10–20 synthetic or authorized records, clearly labeled.

## Open decisions

Each remains open until the founder supplies a decision. These are blockers only for work that depends on them.

| ID | Open decision | Blocks |
|---|---|---|
| OPEN-001 | Initial geography | Geographic validation, location-specific taxonomy and launch data scope |
| OPEN-002 | Canonical area units and currency conventions | Comparable normalization, valuation and finance display/calculation |
| OPEN-003 | Production authentication and organization tenancy | Production user access and data isolation |
| OPEN-004 | Deployment target and managed PostgreSQL provider | Production deployment/configuration; not local schema design |
| OPEN-005 | Valuation methodology and adjustment rules | M3 valuation calculations |
| OPEN-006 | Rent assumptions/methodology | M3 rent calculations |
| OPEN-007 | ROI, MOIC, cash-flow timing, discounting, tax/debt/sale conventions | M4 finance outputs |
| OPEN-008 | Target IRR and maximum-price behavior for edge cases | M5 acquisition price solver |
| OPEN-009 | Data rights/terms for any proposed external source | Any connector or source-specific ingestion |

## Record format

For each resolved decision, add `DEC-###.md` containing:

```text
Date:
Decision:
Context:
Options:
Chosen:
Reason/evidence:
Reversible:
Owner:
```

Do not turn an open item into a hidden default. Use `OPEN DECISION — BLOCKED UNTIL FOUNDER CONFIRMS` or, for source rights, `OPEN DATA / LEGAL REVIEW — BLOCKED` in dependent work.
