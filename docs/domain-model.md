# RET-010 domain model

RET-010 establishes persistent, typed records for organization, user, deal, property, project, developer, location, and micro-market. This is an entity model only. It does not provide login, authorization, organization isolation, or a market/geography taxonomy.

## Entities and implemented relationships

| Entity | Stored fields | Relationships |
|---|---|---|
| Organization | UUID, name, created timestamp | No membership or Deal ownership behavior is inferred. |
| User | UUID, display name, created timestamp | Person record only; no credentials, email identity, roles, or organization membership. |
| Deal | Existing UUID, name, status, timestamps | Existing one-to-one Property remains unchanged. |
| Property | Existing UUID, deal FK, address, city, asset type, area value/unit, timestamps | Existing one-to-one Deal relation and area constraints remain unchanged. |
| Project | UUID, name, optional Developer and Location FKs, created timestamp | Multiple projects may reference the same Developer or Location. The relation is optional. |
| Developer | UUID, name, created timestamp | Project reference is optional; no corporate/legal identity is inferred. |
| Location | UUID, name, optional parent Location, created timestamp | Generic self-referencing hierarchy; no country/state/city enum or geospatial assumptions. |
| MicroMarket | UUID, name, optional Location FK, created timestamp | Optional broad Location association; no canonical boundary or uniqueness rule. |

The Deal and Property API request/response fields are unchanged. New reference APIs provide create, list, and retrieve endpoints for their records. Names are trimmed and required; no global uniqueness policy is imposed.

## Open decisions

- **OPEN DECISION — BLOCKED UNTIL FOUNDER CONFIRMS:** authentication identity and User-to-Organization membership/roles.
- **OPEN DECISION — BLOCKED UNTIL FOUNDER CONFIRMS:** whether Deals are organization-owned and how tenant isolation works.
- **OPEN DECISION — BLOCKED UNTIL FOUNDER CONFIRMS:** whether a Project groups Deals or Properties, and whether a Project can have multiple Developers/Locations.
- **OPEN DECISION — BLOCKED UNTIL FOUNDER CONFIRMS:** canonical Location hierarchy, MicroMarket boundaries, aliases, and mapping of existing free-text Property.city values.
- **OPEN DECISION — BLOCKED UNTIL FOUNDER CONFIRMS:** whether Developer is a company, person, or both and whether it should reference an Organization.

Until those are decided, no API route uses these entities to grant access, scope Deal reads, infer a property's location, or change existing Deal/Property responses.

## Migration

Alembic revision `20260930_0002` adds the six reference tables and justified FK lookup indexes. Downgrade to revision `20260930_0001` removes only RET-010 tables. Downgrade to `base` still removes all tables and data; use only for a disposable database.
