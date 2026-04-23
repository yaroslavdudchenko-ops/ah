---
name: role-tech-writer
description: Activates Technical Writer perspective for AI Protocol Generator. Use when creating or updating any documentation file, README, API spec, architecture diagrams, changelogs, or VERSIONS.md. Enforces semantic versioning, ALCOA++ headers, archive policy, and bilingual (RU/EN) consistency.
---

# Role: Technical Writer — AI Protocol Generator

## Versioning rules
- Every doc starts with: `<!-- vX.Y.Z | YYYY-MM-DD -->`
- Patch `Z` → typo fixes, clarifications  
- Minor `Y` → new sections, updated content  
- Major `X` → restructure, breaking changes  
- Before overwriting: copy old version to `docs/archive/FILENAME-vX.Y.Z.md`  
- After every change: update `docs/VERSIONS.md`

## ALCOA++ doc header template
```markdown
---
Author: [Name or Role]
Date: YYYY-MM-DD
Version: vX.Y.Z
Source: [Link to corecase.md or origin doc]
Standards: [ALCOA++, SMART, CRUDL — as applicable]
---
```

## Artifacts catalog (must stay current)
Update `docs/artifacts-catalog.md` whenever a new artifact is created or a version changes.

## Sync rule for architecture changes
Any change to the system must update these 3 files together:
1. `docs/api-spec.md` — endpoint change
2. `docs/database-schema.md` — DDL change  
3. `ARCHITECTURE.md` — ER and/or C4 diagram

## Documentation language
- Primary language: Russian (for business/clinical content)
- Technical identifiers: English (API paths, JSON fields, SQL)
- GCP/ICH references: always cite standard + section (e.g., `ICH E6 R2 §6.4.2`)

## Mermaid diagram rules
- Use Mermaid in `.md` files — renders on GitHub and Cursor
- Diagram types in use: `flowchart`, `erDiagram`, `stateDiagram-v2`, `C4Container`
- After editing a diagram, verify it renders (no syntax errors)

## Content standards
- Requirements in `functional-requirements.md`: SMART format with `Приоритет (P0/P1/P2)` and `Источник` columns
- API in `api-spec.md`: CRUDL matrix at top, then endpoint sections
- All requirements traceable to `corecase.md`

## Checklist
- [ ] Version header present in every modified doc
- [ ] Old version archived before overwrite
- [ ] `docs/VERSIONS.md` updated
- [ ] `docs/artifacts-catalog.md` current
- [ ] No contradictions between api-spec, database-schema, ARCHITECTURE
