# Database Schema

**Version:** 1.2.0 | **Date:** 2026-04-24 | **Status:** Active  
**Author:** System Architect  
**Source:** [corecase.md](../corecase.md), [functional-requirements.md](functional-requirements.md)  
**Standards:** ALCOA++ (Attributable, Contemporaneous, Complete, Consistent)

База данных: PostgreSQL 16. ORM: SQLAlchemy 2 (async). Миграции: Alembic.

---

## Таблицы

### templates
Шаблоны протоколов по фазам и типам дизайна.

```sql
CREATE TABLE templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(200) NOT NULL,
  phase VARCHAR(10) NOT NULL CHECK (phase IN ('I', 'II', 'III', 'IV')),
  design_type VARCHAR(50) NOT NULL,  -- open_label | randomized | placebo_controlled | double_blind
  section_prompts JSONB NOT NULL,    -- {introduction: "...", objectives: "..."} — промпты под фазу
  created_at TIMESTAMP DEFAULT NOW()
);
```

### protocols
Метаданные протокола. Контент хранится в версиях.

```sql
CREATE TABLE protocols (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(200) NOT NULL,
  phase VARCHAR(10) NOT NULL CHECK (phase IN ('I', 'II', 'III', 'IV')),
  indication TEXT NOT NULL,
  population TEXT NOT NULL,
  inclusion_criteria JSONB DEFAULT '[]',    -- Критерии включения (GCP ICH E6 R2 §4.3 / FR-02.7)
  primary_endpoint TEXT NOT NULL,
  secondary_endpoints JSONB DEFAULT '[]',
  duration_weeks INTEGER NOT NULL CHECK (duration_weeks > 0),  -- единица: недели; пример: 96 = ~22 месяца
  drug_name VARCHAR(200) NOT NULL,
  inn VARCHAR(200),
  dosing TEXT NOT NULL,
  exclusion_criteria JSONB DEFAULT '[]',
  template_id UUID REFERENCES templates(id),
  therapeutic_area VARCHAR(200),              -- Терапевтическая область (онкология, кардиология, ...)
  tags JSONB DEFAULT '[]',                   -- Пользовательские теги (hash-based color в UI)
  created_by VARCHAR(100),                   -- Username создателя (4-eyes principle, FR-09.1) — миграция 004
  status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'generated', 'in_review', 'approved', 'archived')),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_protocols_phase ON protocols(phase);
CREATE INDEX idx_protocols_status ON protocols(status);
```

### protocol_versions
Снапшоты контента. JSONB позволяет добавлять секции без миграции.

```sql
CREATE TABLE protocol_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  protocol_id UUID NOT NULL REFERENCES protocols(id) ON DELETE CASCADE,
  version VARCHAR(20) NOT NULL,    -- v0.1, v0.2, v1.0
  content JSONB NOT NULL,          -- {introduction: "...", objectives: "...", design: "...", ...}
  comment TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(protocol_id, version)
);

CREATE INDEX idx_protocol_versions_protocol ON protocol_versions(protocol_id);
```

**Структура `content` JSONB:**
```json
{
  "introduction": "...",
  "objectives": "...",
  "design": "...",
  "population": "...",
  "dosing": "...",
  "efficacy": "...",
  "safety": "...",
  "statistics": "...",
  "ethics": "...",
  "sap": "...",
  "icf": "..."
}
```

### terminology
Контроль консистентности терминологии (МНН, названия препаратов, эндпоинты).

```sql
CREATE TABLE terminology (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  protocol_id UUID REFERENCES protocols(id) ON DELETE CASCADE,
  term VARCHAR(200) NOT NULL,
  term_type VARCHAR(50) NOT NULL CHECK (term_type IN ('drug', 'inn', 'endpoint', 'population', 'other')),
  preferred_form VARCHAR(200) NOT NULL,
  aliases JSONB DEFAULT '[]',       -- ["BCD-100", "Пролголимаб", "prolgolimab"]
  created_at TIMESTAMP DEFAULT NOW()
);
```

### open_issues
Список открытых вопросов для медицинского ревьюера.

```sql
CREATE TABLE open_issues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  protocol_id UUID NOT NULL REFERENCES protocols(id) ON DELETE CASCADE,
  version_id UUID REFERENCES protocol_versions(id),
  section VARCHAR(100),
  issue TEXT NOT NULL,
  status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'resolved', 'wontfix')),
  resolution_note TEXT,                     -- Комментарий при закрытии (ALCOA++ Attributable)
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()        -- ALCOA++ Contemporaneous: отслеживание смены статуса
);

CREATE INDEX idx_open_issues_protocol ON open_issues(protocol_id);
CREATE INDEX idx_open_issues_status ON open_issues(status);
```

### audit_log
Аудит-трейл всех действий (GCP compliance требование).

```sql
CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type VARCHAR(50) NOT NULL DEFAULT 'protocol',  -- protocol | template | user
  entity_id UUID,                 -- ID сущности (protocol_id и т.п.)
  protocol_id UUID REFERENCES protocols(id),
  action VARCHAR(50) NOT NULL,    -- create | update | delete | ai_generate | consistency_check | export | section_regenerate | approve | copy
  performed_by VARCHAR(100),      -- username (ALCOA++ Attributable)
  role VARCHAR(20),               -- роль пользователя в момент действия
  model VARCHAR(100),             -- AI модель (InHouse/Qwen3.5-122B) — только для AI-действий
  duration_ms INTEGER,            -- время выполнения AI-запроса в мс
  details JSONB DEFAULT '{}',     -- без полного контента документа, без PII
  request_id UUID,                -- для трассировки
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_log_entity ON audit_log(entity_id);
CREATE INDEX idx_audit_log_protocol ON audit_log(protocol_id);
CREATE INDEX idx_audit_log_created ON audit_log(created_at);
CREATE INDEX idx_audit_log_performed_by ON audit_log(performed_by);
```

### protocol_embeddings *(P3 — планируется в v1.2.0, RAG)*
Векторные embeddings для секций протоколов. Используется в RAG.

```sql
-- Требует: pgvector расширение (образ pgvector/pgvector:pg16 вместо postgres:16-alpine)
-- Alembic миграция 005: CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE protocol_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  version_id UUID NOT NULL REFERENCES protocol_versions(id) ON DELETE CASCADE,
  section_key VARCHAR(50) NOT NULL,     -- introduction | objectives | design | ... | sap | icf
  embedding vector(1536),              -- InHouse/embeddings-model-1 (1536 dims)
  model VARCHAR(100) NOT NULL DEFAULT 'InHouse/embeddings-model-1',
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(version_id, section_key)
);

CREATE INDEX idx_embeddings_version ON protocol_embeddings(version_id);
CREATE INDEX idx_embeddings_ivfflat ON protocol_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);
```

**Когда активировать:** similarity-запросы > 100мс ИЛИ корпус > 5000 протоколов.  
**Fallback:** если embedding API недоступен — генерация работает без RAG (graceful degrade).

---

## Миграции Alembic

| Ревизия | Описание | Дата |
|---|---|---|
| 001 | Начальная схема (templates, protocols, protocol_versions, open_issues, audit_log) | 2026-04-23 |
| 002 | Поле tags JSONB в protocols; therapeutic_area | 2026-04-23 |
| 003 | Обновление audit_log: entity_type, entity_id, performed_by, role, model, duration_ms | 2026-04-23 |
| 004 | Поле created_by VARCHAR(100) в protocols (4-eyes principle) | 2026-04-24 |
| 005 | *(Планируется)* CREATE EXTENSION vector + protocol_embeddings | P3/RAG |

---

## Связи

```
templates 1──────────────────── * protocols
protocols 1──────────────────── * protocol_versions
protocols 1──────────────────── * open_issues
protocols 1──────────────────── * terminology
protocols 1──────────────────── * audit_log
protocol_versions 1──────────── * open_issues
protocol_versions 1──────────── * protocol_embeddings  (P3/RAG)
```

---

## Индексы

| Таблица | Индекс | Тип | Цель |
|---|---|---|---|
| protocols | phase | btree | Фильтрация по фазе |
| protocols | status | btree | Фильтрация по статусу |
| protocol_versions | protocol_id | btree | JOIN с protocols |
| open_issues | protocol_id | btree | Быстрый доступ к вопросам |
| open_issues | status | btree | Фильтрация по статусу |
| audit_log | entity_id | btree | Аудит по сущности |
| audit_log | protocol_id | btree | Аудит по протоколу |
| audit_log | created_at | btree | Временные срезы |
| audit_log | performed_by | btree | Фильтрация по пользователю |
| protocol_embeddings | version_id | btree | JOIN с protocol_versions (P3) |
| protocol_embeddings | embedding | ivfflat/cosine | ANN-поиск похожих секций (P3) |
