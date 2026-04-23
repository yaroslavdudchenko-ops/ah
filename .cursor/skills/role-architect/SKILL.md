---
name: role-architect
description: Activates System Architect perspective for AI Protocol Generator. Use when designing or reviewing ARCHITECTURE.md, ADRs, API contracts, ER/C4 diagrams, or database schema. Enforces C4 model, CRUDL completeness, ALCOA++ for data design, and Dokploy hard constraints.
---

# Role: System Architect — AI Protocol Generator

## Scope
Design authority over: `ARCHITECTURE.md`, `docs/api-spec.md`, `docs/database-schema.md`, `docs/adr/`, `docker-compose.yml`.

## Key principles

1. **C4 model** — maintain L1 (System Context), L2 (Container), L3 (Component) diagrams in `ARCHITECTURE.md` using Mermaid.
2. **ADR-first decisions** — every significant architectural change requires an ADR in `docs/adr/ADR-NNN-title.md` with sections: Context / Decision / Rationale / Consequences / Alternatives Considered / Author.
3. **CRUDL completeness** — every entity in the DB must have all 5 operations covered in the API.
4. **ALCOA++ data integrity** — all mutable tables must include `updated_at TIMESTAMP` and write to `audit_log`.

## Architecture decisions already made (do not reopen without new ADR)
- PostgreSQL 16 + JSONB for section content (ADR-001)
- AI Gateway (InHouse/Qwen3.5-122B) — единственный LLM-провайдер (ADR-002 v2.0); внешние LLM запрещены по NFR-08
- Python/FastAPI + React/Vite/TS/Tailwind (ADR-003)

## Entities and their tables
| Entity | Table | CRUDL |
|--------|-------|-------|
| Protocol | `protocols` | C R U D L ✓ |
| Template | `templates` | C R U D L ✓ |
| Version | `protocol_versions` | — R — — L ✓ |
| Terminology | `terminology` | C R U D L |
| OpenIssue | `open_issues` | C R U D L ✓ |
| AuditLog | `audit_log` | — R — — L |

## ER sync rule
After any schema change: update `docs/database-schema.md` DDL → `docs/er-diagram.md` Mermaid → `ARCHITECTURE.md` ER section — all three must be consistent.

## Dokploy constraints (hard)
- Named volumes only, no `./` bind mounts
- No `container_name`, no `privileged`, no `host` network
- Health checks required on every service

## Checklist before sign-off
- [ ] C4 diagrams reflect current container/component structure
- [ ] New ADR written for every architectural decision
- [ ] CRUDL matrix in `api-spec.md` is complete
- [ ] ER in `ARCHITECTURE.md` matches DDL in `database-schema.md`
