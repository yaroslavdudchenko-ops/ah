# CHECKPOINT — Восстановление контекста

**Создан:** 2026-04-23  
**Версия:** 2.0.0  
**Обновлён:** 2026-04-23 (сессия 2)  
**Назначение:** Полное восстановление контекста после очистки чата

---

## 1. Кто ты в этом проекте

Ты — **senior разработчик + бизнес-аналитик из биотех/фарм сферы**, 5+ лет опыта.  
Задача: разработать и задеплоить **AI-генератор протоколов клинических исследований** за **1.5 дня** (дедлайн: 24.04.2026 17:30).

---

## 2. Суть задачи (кейс)

**Проблема:** Команды копируют старые протоколы КИ вручную → "хвосты" от старых дизайнов, несоответствия терминологии, пропущенные GCP/ICH-разделы.

**Решение:** Веб-сервис: структурированный ввод параметров → AI-генерация черновика протокола → контроль консистентности → версионирование → экспорт.

**Обязательные сдаточные артефакты:**
1. Публичный URL работающего сервиса (Dokploy)
2. GitLab репозиторий `gitlab.biocad.ru` с историей коммитов
3. `README.md`
4. `PROMPTS.md`

**AI Gateway (единственный провайдер):** `AI_GATEWAY_URL` + `AI_GATEWAY_API_KEY` → `InHouse/Qwen3.5-122B`  
**Политика ИБ (NFR-08):** внешние LLM (OpenRouter, OpenAI, Anthropic) запрещены в production-коде КИ-системы

---

## 3. Технический стек

| Слой | Технология | ADR |
|---|---|---|
| Backend | Python 3.12 + FastAPI + SQLAlchemy 2 (async) + Alembic | ADR-003 |
| Frontend | React 18 + Vite + TypeScript + Tailwind CSS | ADR-003 |
| База данных | PostgreSQL 16 (JSONB для секций, docker-compose сервис `db`) | ADR-001 |
| AI | AI Gateway → `InHouse/Qwen3.5-122B` (OpenAI-compatible API, только локальные модели) | ADR-002 v2.0 |
| Экспорт | python-docx + Jinja2 + mistune (Markdown→HTML) | — |
| Deploy | Dokploy (Docker Compose mode) + Traefik | DEPLOY.md |

**3 Docker-сервиса:** `frontend` (nginx:alpine), `backend` (python:3.12-slim), `db` (postgres:16-alpine)

### AI-провайдер — только внутренний Gateway

```
Backend → AIGatewayClient (httpx.AsyncClient + tenacity retry)
            ↓ POST ${AI_GATEWAY_URL}/v1/chat/completions
            ↓ Retry × 3 (exponential backoff)
            ↓ При исчерпании попыток → HTTP 503 (НЕ fallback на внешние LLM)
```

**Внешние LLM (OpenRouter, OpenAI, Anthropic) запрещены по NFR-08 / ADR-002.**

---

## 4. Конфигурация (mcp.json + .env.example)

### mcp.json (корень проекта)

| Сервер | Пакет | Назначение |
|---|---|---|
| `chrome-devtools` | `chrome-devtools-mcp` | Отладка frontend |
| `mcp-atlassian` | `mcp-atlassian` | Jira / Confluence |
| `gitlab` | `@modelcontextprotocol/server-gitlab` | GitLab API (gitlab.biocad.ru) |
| `provider.gateway` | `@ai-sdk/openai-compatible` | AI Gateway → Qwen3.5-122B |

Ключ конфигурации: `"mcpServers"` (исправлено с `"mcp"`).

### .env.example — ключевые переменные

```
AI_GATEWAY_URL=            # Внутренний AI Gateway URL
AI_GATEWAY_API_KEY=        # Ключ доступа к Gateway
GITLAB_API_URL=https://gitlab.biocad.ru
GITLAB_PERSONAL_ACCESS_TOKEN=   # PAT: api + read_repository
OPENROUTER_API_KEY=        # dev/config only — не используется приложением в production
POSTGRES_PASSWORD=         # REQUIRED
```

---

## 5. Текущее состояние

### Фаза 0 — Документация ✅ 100%

| Файл | Версия | Статус |
|---|---|---|
| `README.md` | 1.0.0 | ✅ Обновлён (AI Gateway, без OpenRouter) |
| `ARCHITECTURE.md` | **1.2.0** | ✅ C4 L1/L2/L3 + ER + Deploy, только AI Gateway |
| `DEPLOY.md` | 1.0.0 | ✅ AI Gateway переменные, без OpenRouter |
| `PROMPTS.md` | 1.0.0 | ✅ Структура есть |
| `.env.example` | 2.0.0 | ✅ AI Gateway + GitLab + OpenRouter (dev-only) |
| `mcp.json` | 1.1.0 | ✅ mcpServers: GitLab + chrome + atlassian |
| `docs/functional-requirements.md` | **1.2.0** | ✅ 12 секций, NFR-07 (РФ), NFR-08 (ИБ) |
| `docs/api-spec.md` | **1.2.0** | ✅ CRUDL + AI Provider (только Gateway) |
| `docs/business-requirements.md` | 1.0.0 | ✅ |
| `docs/artifacts-catalog.md` | **1.1.0** | ✅ A-007 v1.2.0, A-009 v1.2.0, S-004 v2.0.0 |
| `docs/adr/ADR-002` | **v2.0.0** | ✅ Переписан: AI Gateway only, внешние LLM запрещены |
| Все прочие docs/* | 1.0.0 | ✅ ER, Event Storming, Use Case, State, Test Plan… |

---

### Фаза 1 — Backend ✅ 100% (завершена 23.04.2026)

| Файл | Описание |
|---|---|
| `docker-compose.yml` | 3 сервиса: db, backend, frontend. Named volumes. Short ports. HEALTHCHECK. |
| `backend/Dockerfile` | python:3.12-slim, non-root user, alembic upgrade head + uvicorn |
| `frontend/Dockerfile` | node:20-alpine builder → nginx:alpine, non-root |
| `frontend/nginx.conf` | SPA fallback + `/api/` proxy → backend:8000 |
| `backend/app/core/config.py` | pydantic-settings: AI_GATEWAY_URL/KEY/MODEL, DATABASE_URL, CORS |
| `backend/app/core/database.py` | async_engine, AsyncSessionLocal, get_db() dependency |
| `backend/app/models/protocol.py` | 5 таблиц: Protocol, ProtocolVersion, Template, OpenIssue, AuditLog |
| `backend/app/schemas/protocol.py` | Pydantic v2: Create/Update/Response + error_body() |
| `backend/app/schemas/generate.py` | GenerateRequest/Status, CheckResponse, DiffResponse (P2 stub) |
| `backend/app/services/ai_gateway.py` | AIGatewayClient: httpx + tenacity ×3. Только Qwen. HTTP 503 при сбое. |
| `backend/app/services/generator.py` | 12 секций, MVP=7, THERAPEUTIC_AREA/PHASE контексты, fallback |
| `backend/app/services/consistency.py` | GCP+RF check, JSON парсинг, fallback при недоступности |
| `backend/app/services/export_service.py` | MD ✅ HTML ✅ DOCX ✅ (P2, готов к включению) |
| `backend/app/routers/health.py` | GET /health |
| `backend/app/routers/protocols.py` | CRUDL + /versions + /diff stub → 501 |
| `backend/app/routers/generate.py` | POST /generate (async BackgroundTask) + GET status |
| `backend/app/routers/check.py` | POST /check → consistency + open_issues persist |
| `backend/app/routers/export.py` | GET /export?format=md\|html\|docx |
| `backend/app/routers/templates.py` | GET /templates, POST stub → 501 |
| `backend/app/main.py` | FastAPI app, CORS, global error handler, lifespan |
| `backend/alembic/env.py` | Async alembic env |
| `backend/alembic/versions/001_initial_schema.py` | 5 таблиц + индексы + 3 seed templates |

**P2 готовность в коде:**
- DOCX: реализован в `export_service.py`, включить снятием `NotImplementedError`
- Diff: схемы готовы в `schemas/generate.py`, endpoint-stub в `protocols.py`
- SAP/ICF: добавить эндпоинты + секции в `generator.py` (SECTION_PROMPTS готов к расширению)

---

### Фаза 1.5 — Swagger Verification 🔲 0% (следующий шаг после запуска backend)

Обязательная фаза перед началом Frontend. Цель — убедиться, что все P0 эндпоинты backend работают корректно до того, как frontend начнёт на них завязываться.

| Проверка | Эндпоинт | Ожидаемый результат |
|---|---|---|
| Health check | `GET /health` | `{"status":"ok","db":"connected"}` |
| Создание протокола | `POST /api/v1/protocols` | 201 + `{id, title, status}` |
| Список протоколов | `GET /api/v1/protocols` | 200 + `[...]` |
| Запуск генерации | `POST /api/v1/protocols/{id}/generate` | 202 + `{task_id}` |
| Статус генерации | `GET /api/v1/protocols/{id}/generate/{task_id}` | 200 + `{status, sections_done}` |
| Проверка консистентности | `POST /api/v1/protocols/{id}/check` | 200 + `{compliance_score, issues}` |
| Экспорт MD | `GET /api/v1/protocols/{id}/export?format=md` | 200 + файл |
| Экспорт HTML | `GET /api/v1/protocols/{id}/export?format=html` | 200 + файл |
| Список шаблонов | `GET /api/v1/templates` | 200 + 3 шаблона (seed) |
| Swagger UI | `GET /docs` | Интерактивная документация FastAPI |

**Инструменты:** Swagger UI (`/docs`), `backend/tests/smoke_test.http` (REST Client), `curl`

**Статус:** Не выполнена — backend не запущен (docker-compose.yml есть, но compose не поднят)

---

### Фаза 2 — Frontend 🔲 0% (после Фазы 1.5)

- `frontend/src/` — не создан
- React + Vite + TypeScript + Tailwind — не инициализирован
- Форма ввода параметров — не создана
- Viewer протокола — не создан
- Экспорт MD/HTML — не создан

---

### Фаза 2.5 — QA Testing 🔲 0% (после Фазы 2 Frontend)

> **Правило:** Фаза тестирования обязательна перед деплоем. Без прохождения P0-критериев деплой не начинается.

#### 2.5.1 Автотесты (pytest)

```bash
# Запуск из backend-контейнера
docker compose exec backend pytest tests/ -v --cov=app --cov-report=term-missing
```

| Файл | Что тестирует | Маркер |
|---|---|---|
| `tests/test_health.py` | `GET /health` → 200 | integration |
| `tests/test_protocols.py` | CRUDL + валидация + 404 + ALT | integration |
| `tests/test_export.py` | MD/HTML структура, export before generate | integration + unit |
| `tests/test_ai_gateway.py` | retry, fallback, section count | unit |
| `tests/test_templates.py` | seed шаблоны, 501-stub | integration |

**Целевое покрытие:** `services/ai_gateway.py` ≥90%, `routers/protocols.py` ≥80%

#### 2.5.2 Ручной прогон (Happy Path)

| # | Сценарий | Dataset | Файл |
|---|---|---|---|
| HP-01 | Создать → Сгенерировать → Экспорт MD/HTML | Dataset-1 (BCD-100, Phase II) | `docs/test-plan.md §4` |
| HP-02 | Полный жизненный цикл Phase III | Dataset-2 (BCD-089, Phase III) | `docs/test-plan.md §4` |

#### 2.5.3 Альтернативные сценарии (обязательные)

| Группа | Описание | Ref |
|---|---|---|
| ALT-01 | Валидация формы: пустые поля, phase=IV, duration=0 | `docs/test-plan.md §5` |
| ALT-02 | AI Gateway fallback: нет 500, есть шаблонный текст | `docs/test-plan.md §5` |
| ALT-03 | Export before generate → 422 NO_CONTENT | `docs/test-plan.md §5` |
| ALT-04 | Несуществующий ресурс → 404 с error body | `docs/test-plan.md §5` |
| ALT-08 | DELETE + GET после удаления → 404 | `docs/test-plan.md §5` |

#### 2.5.4 Критерии приёмки Фазы 2.5

- [ ] HP-01 и HP-02 пройдены полностью
- [ ] Нет HTTP 500 во всём Happy Path
- [ ] AI Gateway fallback работает без 500 (ALT-02)
- [ ] pytest unit-тесты: 0 failures, 0 errors
- [ ] Нет ошибок в консоли браузера при HP-01

**Документ QA:** `docs/test-plan.md` v2.0.0

---

### Фаза 3 — Deploy 🔲 0%

- Dokploy — не настроен
- Публичный URL — отсутствует
- GitLab CI — не создан

---

### Фаза 4 — P1 features 🔲 0%

- Версионирование (UI) — backend готов, frontend нет
- Consistency check UI — backend готов, frontend нет
- HTML экспорт (кнопка в UI) — backend готов

---

### Фаза 5 — P2 features 🔲 0% (если останется время)

- DOCX экспорт — backend готов (снять заглушку)
- SAP/ICF генерация — добавить промпты + эндпоинты
- Diff UI — схемы готовы, нужен frontend + диффер

---

## 6. Роли проекта

| Роль | Rule | Skill |
|---|---|---|
| System Architect | `.cursor/rules/role-architect.mdc` | `.cursor/skills/role-architect/SKILL.md` |
| Backend Developer | `.cursor/rules/role-backend.mdc` | `.cursor/skills/role-backend/SKILL.md` |
| Frontend Developer | `.cursor/rules/role-frontend.mdc` | `.cursor/skills/role-frontend/SKILL.md` |
| AI Engineer | `.cursor/rules/role-ai-engineer.mdc` | `.cursor/skills/role-ai-engineer/SKILL.md` |
| QA Engineer | `.cursor/rules/role-qa.mdc` | `.cursor/skills/role-qa/SKILL.md` |
| Technical Writer | `.cursor/rules/role-tech-writer.mdc` | `.cursor/skills/role-tech-writer/SKILL.md` |
| DevOps Engineer | `.cursor/rules/role-devops.mdc` | `.cursor/skills/role-devops/SKILL.md` |
| Senior Clinical Research Analyst | `.cursor/rules/role-clinical-analyst.mdc` | `.cursor/skills/role-clinical-analyst/SKILL.md` |
| Information Security Specialist | `.cursor/rules/role-infosec.mdc` | `.cursor/skills/role-infosec/SKILL.md` |

Также активны глобальные правила: `.cursor/rules/00-security.mdc`, `99-forbidden.mdc`.

---

## 7. Ключевые ограничения (нельзя менять)

### Архитектурные
1. **PostgreSQL** — финальный выбор, не SQLite
2. **AI Gateway** (единственный провайдер) → `InHouse/Qwen3.5-122B`, fallback на внешние LLM запрещён
3. **Dokploy** — деплой-платформа (не Vercel, не Railway)
4. **GitLab** `gitlab.biocad.ru` — репозиторий (не GitHub)

### Docker/Dokploy (hard constraints)
5. **Без `container_name`** в docker-compose
6. **Порты short syntax** `- "80"` — без `80:80`
7. **Named volumes only** `db-data` — не `./` пути
8. **Non-root user** в Dockerfile — обязательно
9. **HEALTHCHECK** для каждого сервиса

### Качество кода
10. **Отклонение от FR ≤ 15%** для обычных функций, **≤ 25%** для AI-генератора (NFR-06)
11. **English naming** — таблицы БД, колонки, Python-код, API endpoints
12. **ALCOA++ / SMART / CRUDL** — все документы и API

---

## 8. Демо-данные (синтетические)

**Протокол 1 — Фаза II, Онкология:**
- Препарат: BCD-100 (Пролголимаб, PD-1 ингибитор)
- Индикация: Метастатическая меланома, прогрессия после 1 линии
- Primary endpoint: ORR по RECIST 1.1
- Длительность: 96 недель, доза: 1 мг/кг в/в Q2W

**Протокол 2 — Фаза III, Дерматология:**
- Препарат: BCD-089 (IL-17A ингибитор)
- Индикация: Псориаз среднетяжёлый и тяжёлый (PASI ≥12)
- Primary endpoint: PASI 75 на 12 неделе
- Дизайн: Рандомизированное двойное слепое

---

## 9. Правила проекта (rules/)

| Файл | Содержание |
|---|---|
| `rules/00-project-context.mdc` | Контекст проекта, цели |
| `rules/01-security.mdc` | Безопасность: no secrets in git, watermark, audit_log |
| `rules/02-architecture.mdc` | Архитектурные принципы, ADR формат |
| `rules/03-roles.mdc` | Роли + RACI + corecase-gate checkpoints |
| `rules/04-process.mdc` | Фазы 0-8 + Фаза 1.5 (Swagger) + Фаза 4.5 (Design System) |
| `rules/05-ai-compliance.mdc` | Промпты, `therapeutic_area_context`, `phase_context` |
| `rules/06-development-rules.mdc` | RESTful API, naming (English), Docker, artifact standards |

---

## 10. Структура файлов проекта

```
c:\research-protocols-23042026\
├── README.md
├── ARCHITECTURE.md          ← v1.1.0: C4 + AI Gateway + GitLab
├── DEPLOY.md
├── PROMPTS.md
├── RELEASE-NOTES.md
├── CHECKPOINT.md            ← v2.0.0: этот файл
├── corecase.md
├── mcp.json                 ← v1.1.0: GitLab + AI Gateway
├── .env.example             ← v2.0.0: AI Gateway + GitLab vars
├── config.bat               ← Windows setup script
├── backend/
│   ├── README.md
│   └── requirements.txt
├── frontend/
│   └── README.md
├── prompts/
│   ├── system-prompt.md
│   ├── section-generators/introduction.md
│   └── validation-prompts/
│       ├── consistency-check.md
│       └── gcp-compliance.md
├── canvases/
│   ├── protocol-generator-ui.canvas.tsx   ← UI/UX mockup
│   └── c4-architecture.canvas.tsx         ← C4 интерактивная схема
├── docs/
│   ├── artifacts-catalog.md
│   ├── functional-requirements.md
│   ├── api-spec.md                        ← v1.2.0: AI Provider table
│   ├── database-schema.md
│   ├── business-requirements.md
│   ├── design-system-plan.md
│   ├── clinical-review.md
│   ├── er-diagram.md
│   ├── event-storming.md
│   ├── user-story-map.md
│   ├── state-diagram.md
│   ├── use-case.md
│   ├── ui-ux-brief.md
│   ├── test-plan.md
│   ├── review-rules-applied.md
│   ├── VERSIONS.md
│   ├── adr/
│   │   ├── ADR-001-postgresql.md
│   │   ├── ADR-002-openrouter.md
│   │   └── ADR-003-stack.md
│   └── archive/
├── rules/
│   ├── 00-project-context.mdc
│   ├── 01-security.mdc
│   ├── 02-architecture.mdc
│   ├── 03-roles.mdc
│   ├── 04-process.mdc
│   ├── 05-ai-compliance.mdc
│   └── 06-development-rules.mdc
├── .cursor/
│   ├── rules/
│   │   ├── 00-security.mdc
│   │   ├── 99-forbidden.mdc
│   │   ├── role-architect.mdc
│   │   ├── role-backend.mdc
│   │   ├── role-frontend.mdc
│   │   ├── role-ai-engineer.mdc
│   │   ├── role-qa.mdc
│   │   ├── role-tech-writer.mdc
│   │   ├── role-devops.mdc
│   │   ├── role-clinical-analyst.mdc
│   │   └── role-infosec.mdc
│   ├── skills/
│   │   ├── role-architect/SKILL.md
│   │   ├── role-backend/SKILL.md
│   │   ├── role-frontend/SKILL.md
│   │   ├── role-ai-engineer/SKILL.md
│   │   ├── role-qa/SKILL.md
│   │   ├── role-tech-writer/SKILL.md
│   │   ├── role-devops/SKILL.md
│   │   ├── role-clinical-analyst/SKILL.md
│   │   └── role-infosec/SKILL.md
│   └── commands/
│       └── security-audit.md
└── dokploy-repo-prep/SKILL.md
```

---

## 11. Следующие шаги (Фаза 1 — старт кодирования)

```
Час 0-2:   docker-compose.yml + Dockerfile backend + Dockerfile frontend + nginx.conf
Час 2-5:   backend: main.py, models, schemas, CRUD /api/v1/protocols + /templates
Час 5-9:   backend: AIGatewayClient (primary→fallback) + /generate endpoint
Час 9-10:  Фаза 1.5: Swagger UI проверка всех эндпоинтов
Час 10-13: frontend: Protocol list + Create form + Protocol viewer
Час 13-15: frontend: Export MD + HTML + деплой первой версии
Час 15-16: Фаза 4.5: Design System (Tailwind tokens + atomic components)
Час 16-18: Докплой деплой + GitLab push + публичный URL
Час 18-22: DOCX export + версионирование + консистентность
Час 22-25: Diff viewer + UI polish (Design System применить)
Час 25-27: Stretch: SAP/ICF + финальный README/PROMPTS + сдача
```

---

## 12. Что читать первым при восстановлении

1. `CHECKPOINT.md` — этот файл
2. `corecase.md` — задание и анализ
3. `mcp.json` — интеграции (AI Gateway, GitLab)
4. `docs/user-story-map.md` — MVP приоритеты и тайминг
5. `ARCHITECTURE.md` — актуальная схема C4 с AI Gateway
6. `DEPLOY.md` + `dokploy-repo-prep/SKILL.md` — деплой

---

## 13. Dokploy-специфика (из SKILL.md)

Скилл: `c:\research-protocols-23042026\dokploy-repo-prep\SKILL.md`

- AutoDeploy = `rm -rf` + `git clone` каждый раз → `./` volume paths ломаются
- `env -i` при деплое — только `.env` файл доходит до контейнера
- Домены = Traefik labels → обязателен редеплой после изменения домена
- Isolated Deployment рекомендован (Advanced → Enable)

---

## 14. Ключевые изменения сессии 2 (2026-04-23)

| Что | Что изменилось |
|---|---|
| `mcp.json` | Ключ `"mcp"` → `"mcpServers"`, добавлен GitLab MCP (`@modelcontextprotocol/server-gitlab`) |
| `.env.example` | Пересобран: добавлены `AI_GATEWAY_URL`, `AI_GATEWAY_API_KEY`, `GITLAB_API_URL`, `GITLAB_PERSONAL_ACCESS_TOKEN` |
| `ARCHITECTURE.md` | v1.0.0 → **v1.1.0**: AI Gateway во всех 5 диаграммах (L1, L2, L3, ER без изменений, Deploy); GitHub → GitLab |
| `docs/api-spec.md` | v1.2.0: AI Provider — только AI Gateway (InHouse/Qwen3.5-122B), внешние LLM запрещены |
| `CHECKPOINT.md` | v1.0.0 → **v2.0.0**: полное обновление |
