# A-004: ER Diagram

**Version:** 1.0.0 | **Date:** 2026-04-23 | **Status:** Draft  
**Artifact ID:** A-004  
**Связанный документ:** [docs/database-schema.md](database-schema.md) — полная DDL-схема

---

## ER-диаграмма

```mermaid
erDiagram

  templates {
    uuid id PK
    varchar name
    varchar phase "I | II | III | IV"
    varchar design_type "open_label | randomized | placebo_controlled | double_blind"
    jsonb section_prompts "промпты под каждую секцию"
    timestamp created_at
  }

  protocols {
    uuid id PK
    varchar title
    varchar phase "I | II | III | IV"
    text indication
    text population
    text primary_endpoint
    jsonb secondary_endpoints "[]"
    int duration_weeks
    varchar drug_name
    varchar inn "МНН"
    text dosing
    jsonb exclusion_criteria "[]"
    uuid template_id FK
    varchar status "draft | generating | generated | in_review | final"
    timestamp created_at
    timestamp updated_at
  }

  protocol_versions {
    uuid id PK
    uuid protocol_id FK
    varchar version "v0.1, v0.2..."
    jsonb content "секции протокола"
    text comment
    timestamp created_at
  }

  terminology {
    uuid id PK
    uuid protocol_id FK
    varchar term
    varchar term_type "drug | inn | endpoint | population | other"
    varchar preferred_form
    jsonb aliases "[]"
    timestamp created_at
  }

  open_issues {
    uuid id PK
    uuid protocol_id FK
    uuid version_id FK
    varchar section
    text issue
    varchar status "open | resolved | wontfix"
    timestamp created_at
  }

  audit_log {
    uuid id PK
    uuid protocol_id FK
    varchar action "CREATE | UPDATE | GENERATE | EXPORT | CHECK"
    jsonb details
    uuid request_id
    timestamp created_at
  }

  templates ||--o{ protocols : "используется в"
  protocols ||--o{ protocol_versions : "имеет версии"
  protocols ||--o{ terminology : "содержит термины"
  protocols ||--o{ open_issues : "содержит вопросы"
  protocols ||--o{ audit_log : "аудируется"
  protocol_versions ||--o{ open_issues : "относится к версии"
```

---

## Ключевые решения схемы

| Решение | Обоснование |
|---|---|
| `content JSONB` в `protocol_versions` | Гибкость секций без миграций; diff на уровне Python |
| `terminology` как отдельная таблица | Консистентность МНН/названий — ядро GCP-требования |
| `audit_log` отдельно | GCP E6 требует immutable trail всех изменений |
| `status` в `protocols` | State machine для управления жизненным циклом |
| `UNIQUE(protocol_id, version)` | Версия в рамках протокола уникальна |

---

> Полная DDL с индексами и CHECK constraints: [docs/database-schema.md](database-schema.md)
