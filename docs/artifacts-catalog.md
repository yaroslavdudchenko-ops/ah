# Artifacts Catalog

**Version:** 1.1.0 | **Date:** 2026-04-23 | **Status:** Active

Единый реестр всех проектных артефактов с номерами, статусами и ссылками.

---

## Каталог

| ID | Артефакт | Файл | Версия | Статус | Существует |
|---|---|---|---|---|---|
| **A-001** | Event Storming | [docs/event-storming.md](event-storming.md) | 1.0.0 | Draft | ✅ |
| **A-002** | User Story Map | [docs/user-story-map.md](user-story-map.md) | 1.0.0 | Draft | ✅ |
| **A-003** | State Diagram | [docs/state-diagram.md](state-diagram.md) | 1.0.0 | Draft | ✅ |
| **A-004** | ER Diagram | [docs/er-diagram.md](er-diagram.md) | 1.0.0 | Draft | ✅ |
| **A-005** | Use Case Diagram | [docs/use-case.md](use-case.md) | 1.0.0 | Draft | ✅ |
| **A-006** | Functional Requirements | [docs/functional-requirements.md](functional-requirements.md) | 1.2.0 | Draft | ✅ |
| **A-012** | Business Requirements | [docs/business-requirements.md](business-requirements.md) | 1.0.0 | Draft | ✅ |
| **A-007** | Architecture Model (C4) | [ARCHITECTURE.md](../ARCHITECTURE.md) | 1.2.0 | Draft | ✅ |
| **A-008** | UI Mockup & UX Brief | [docs/ui-ux-brief.md](ui-ux-brief.md) | 1.0.0 | Draft | ✅ |
| **A-009** | API Documentation | [docs/api-spec.md](api-spec.md) | 1.2.0 | Draft | ✅ |
| **A-010** | Release Notes | [RELEASE-NOTES.md](../RELEASE-NOTES.md) | 1.0.0 | Draft | ✅ |
| **A-011** | Test Plan | [docs/test-plan.md](test-plan.md) | 1.0.0 | Draft | ✅ |

---

## Вспомогательные артефакты

| ID | Артефакт | Файл | Версия | Статус |
|---|---|---|---|---|
| **S-001** | Database Schema (DDL) | [docs/database-schema.md](database-schema.md) | 1.0.0 | Draft |
| **S-002** | Deploy Guide | [DEPLOY.md](../DEPLOY.md) | 1.0.0 | Draft |
| **S-003** | ADR-001: PostgreSQL | [docs/adr/ADR-001-postgresql.md](adr/ADR-001-postgresql.md) | 1.0.0 | Accepted |
| **S-004** | ADR-002: AI Gateway only (v2.0) | [docs/adr/ADR-002-openrouter.md](adr/ADR-002-openrouter.md) | 2.0.0 | Accepted |
| **S-005** | ADR-003: Stack | [docs/adr/ADR-003-stack.md](adr/ADR-003-stack.md) | 1.0.0 | Accepted |
| **S-006** | Prompts Library | [prompts/](../prompts/) | 1.0.0 | Draft |
| **S-007** | Project Case | [corecase.md](../corecase.md) | 1.0.0 | Active |
| **S-008** | Rules Review | [docs/review-rules-applied.md](review-rules-applied.md) | 1.0.0 | Active |
| **S-009** | Versions Registry | [docs/VERSIONS.md](VERSIONS.md) | 1.0.0 | Active |
| **S-010** | Clinical Review (Corecase-gate) | [docs/clinical-review.md](clinical-review.md) | 1.0.0 | Active |
| **S-011** | Design System Plan | [docs/design-system-plan.md](design-system-plan.md) | 1.0.0 | Planned |
| **S-012** | OpenAPI Spec (generated) | [docs/openapi.json](openapi.json) | — | Pending (Phase 1.5) |
| **S-013** | RF Protocol Sections Reference | [docs/rf-protocol-sections-reference.md](rf-protocol-sections-reference.md) | 1.0.0 | Active |
| **S-014** | RF Protocol Comprehensive Guide | [docs/rf-protocol-guide.md](rf-protocol-guide.md) | 1.0.0 | Active |

---

## Статусы

| Статус | Описание |
|---|---|
| `Draft` | Документ создан, требует уточнений в процессе разработки |
| `Active` | Живой документ, регулярно обновляется |
| `Accepted` | Решение принято, не меняется без нового ADR |
| `Final` | Финальная версия, изменения только через архив |

---

## Правила работы с каталогом

1. При создании нового артефакта — добавить строку в таблицу
2. При выпуске новой версии — обновить `Версия` в таблице
3. При архивировании — переместить запись в `docs/archive/`, пометить статус `Archived`
4. Нумерация: A-### для основных, S-### для вспомогательных
