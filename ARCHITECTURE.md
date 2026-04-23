# Архитектура: AI-генератор протоколов клинических исследований

**Version:** 1.2.0 | **Date:** 2026-04-23 | **Status:** Draft

---

## C4 Level 1 — System Context

```mermaid
C4Context
  title System Context — AI Protocol Generator

  Person(researcher, "Исследователь / КМ", "Составляет черновик протокола КИ")
  Person(reviewer, "Медицинский ревьюер", "Проверяет и комментирует протокол")

  System(app, "Protocol Generator", "Веб-сервис генерации и версионирования протоколов КИ")

  System_Ext(gateway, "AI Gateway", "Внутренний шлюз: InHouse/Qwen3.5-122B (только локальные модели)")
  System_Ext(gitlab, "GitLab (gitlab.biocad.ru)", "Корпоративный репозиторий, CI/CD")
  System_Ext(dokploy, "Dokploy", "Платформа деплоя (Docker Compose)")

  Rel(researcher, app, "Вводит параметры, запускает генерацию")
  Rel(reviewer, app, "Читает список открытых вопросов, оставляет комментарии")
  Rel(app, gateway, "POST /v1/chat/completions", "HTTPS/JSON")
  Rel(app, gitlab, "git push")
  Rel(dokploy, gitlab, "git clone on deploy")
```

---

## C4 Level 2 — Container

```mermaid
C4Container
  title Container Diagram — Protocol Generator

  Person(researcher, "Исследователь / КМ")

  Container_Boundary(app, "Protocol Generator") {
    Container(frontend, "Frontend", "React 18 + Vite + TypeScript + Tailwind", "SPA: форма ввода, редактор секций, diff, экспорт")
    Container(nginx, "nginx", "nginx:alpine", "Раздаёт статику React, проксирует /api → backend")
    Container(backend, "Backend", "Python 3.12 + FastAPI", "REST API: генерация, версионирование, экспорт, консистентность")
    ContainerDb(db, "Database", "PostgreSQL 16", "Протоколы, версии (JSONB), шаблоны, open issues")
  }

  System_Ext(gateway, "AI Gateway", "Внутренний шлюз: InHouse/Qwen3.5-122B (только локальные модели)")

  Rel(researcher, nginx, "HTTPS", "браузер")
  Rel(nginx, frontend, "static files")
  Rel(nginx, backend, "/api/*", "reverse proxy")
  Rel(backend, db, "SQLAlchemy + asyncpg", "TCP 5432")
  Rel(backend, gateway, "POST /v1/chat/completions", "HTTPS")
```

---

## C4 Level 3 — Components (Backend)

```mermaid
C4Component
  title Component Diagram — FastAPI Backend

  Container_Boundary(backend, "Backend (FastAPI)") {

    Component(api_protocols, "Protocols Router", "FastAPI APIRouter", "CRUD протоколов и версий")
    Component(api_generate, "Generate Router", "FastAPI APIRouter", "Запуск AI-генерации секций")
    Component(api_export, "Export Router", "FastAPI APIRouter", "Экспорт MD / HTML / DOCX")
    Component(api_templates, "Templates Router", "FastAPI APIRouter", "Библиотека шаблонов по фазам")

    Component(svc_generator, "GeneratorService", "Python class", "Формирует промпты под фазу и индикацию, вызывает AI")
    Component(svc_consistency, "ConsistencyService", "Python class", "Проверяет единство терминологии, находит противоречия")
    Component(svc_export, "ExportService", "Python class", "python-docx, markdown, jinja2 HTML")
    Component(svc_diff, "DiffService", "Python class", "difflib — diff секций между версиями")

    Component(ai_client, "AIGatewayClient", "httpx.AsyncClient", "POST /v1/chat/completions → AI Gateway (InHouse/Qwen3.5-122B)")

    Component(models, "SQLAlchemy Models", "ORM", "Protocol, ProtocolVersion, Template, OpenIssue, Terminology, AuditLog")
  }

  ContainerDb(db, "PostgreSQL 16")
  System_Ext(gateway, "AI Gateway — InHouse/Qwen3.5-122B")

  Rel(api_protocols, models, "async CRUD")
  Rel(api_generate, svc_generator, "await generate()")
  Rel(api_export, svc_export, "await export()")
  Rel(api_protocols, svc_diff, "await diff()")

  Rel(svc_generator, ai_client, "await complete()")
  Rel(svc_consistency, ai_client, "await check()")
  Rel(svc_generator, models, "save version")

  Rel(models, db, "asyncpg")
  Rel(ai_client, gateway, "HTTPS")
```

---

## Data Model

```mermaid
erDiagram
  templates {
    uuid id PK
    varchar name
    varchar phase
    varchar design_type
    jsonb section_prompts
    timestamp created_at
  }

  protocols {
    uuid id PK
    text title
    varchar phase
    text indication
    text population
    jsonb inclusion_criteria
    text primary_endpoint
    jsonb secondary_endpoints
    int duration_weeks
    varchar drug_name
    varchar inn
    text dosing
    jsonb exclusion_criteria
    uuid template_id FK
    varchar status
    timestamp created_at
    timestamp updated_at
  }

  protocol_versions {
    uuid id PK
    uuid protocol_id FK
    varchar version
    jsonb content
    text comment
    timestamp created_at
  }

  open_issues {
    uuid id PK
    uuid protocol_id FK
    uuid version_id FK
    text section
    text issue
    varchar status
    text resolution_note
    timestamp created_at
    timestamp updated_at
  }

  terminology {
    uuid id PK
    uuid protocol_id FK
    varchar term
    varchar term_type
    varchar preferred_form
    jsonb aliases
    timestamp created_at
  }

  audit_log {
    uuid id PK
    uuid protocol_id FK
    varchar action
    jsonb details
    uuid request_id
    timestamp created_at
  }

  templates ||--o{ protocols : "used by"
  protocols ||--o{ protocol_versions : "has versions"
  protocols ||--o{ open_issues : "has issues"
  protocol_versions ||--o{ open_issues : "linked to version"
  protocols ||--o{ terminology : "has terminology"
  protocols ||--o{ audit_log : "audited by"
```

---

## Deploy (Docker Compose на Dokploy)

```mermaid
graph TD
  GL["GitLab\ngitlab.biocad.ru"]
  DP["Dokploy\nAutoDeploy"]
  TR["Traefik\nreverse proxy"]
  FE["frontend\nnginx:alpine\nport 80"]
  BE["backend\npython:3.12-slim\nport 8000"]
  DB["db\npostgres:16-alpine\nport 5432"]
  VOL[("db-data\nnamed volume")]
  GW["AI Gateway\nInHouse/Qwen3.5-122B\n(только локальные модели)"]

  GL -->|git clone on push| DP
  DP -->|docker compose up| FE
  DP -->|docker compose up| BE
  DP -->|docker compose up| DB
  TR -->|HTTPS| FE
  FE -->|/api proxy| BE
  BE -->|asyncpg| DB
  DB --- VOL
  BE -->|POST /v1/chat/completions| GW
```
