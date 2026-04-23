# CHECKPOINT — Восстановление контекста

**Создан:** 2026-04-23  
**Версия:** 4.0.0  
**Обновлён:** 2026-04-23 (сессия 4 — Auth/RBAC, missing features, test suite)  
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

## 4. Конфигурация (.env + docker-compose)

### Локальная разработка (.env — не в git)

```
AI_GATEWAY_URL=            # Внутренний AI Gateway URL
AI_GATEWAY_API_KEY=        # Ключ доступа к Gateway
POSTGRES_USER=app
POSTGRES_PASSWORD=app_dev_password
POSTGRES_DB=protocols
DATABASE_URL=postgresql+asyncpg://app:app_dev_password@db:5432/protocols
CORS_ORIGINS=["http://localhost","http://localhost:80","http://localhost:8000"]
```

### docker-compose.yml — важные нюансы

- `CORS_ORIGINS` передаётся как JSON-строка: `'["http://localhost","http://localhost:80"]'`
- Порты меняются при каждом `docker compose restart` (random port mapping)
- Backend текущий порт: **50159** (может измениться при рестарте)
- Frontend текущий порт: **56403** (nginx, production-like)
- Vite dev server: **http://localhost:5174/** (для локальной разработки)

---

## 5. Текущее состояние проекта

### Фаза 0 — Документация ✅ 100%

Все документы в `docs/`, включая `test-plan.md` v2.0.0, `api-spec.md` v1.2.0, `ARCHITECTURE.md` v1.2.0.

---

### Фаза 1 — Backend ✅ 100% (завершена 23.04.2026)

| Файл | Описание |
|---|---|
| `docker-compose.yml` | 3 сервиса: db, backend, frontend. Named volumes. HEALTHCHECK. |
| `backend/Dockerfile` | python:3.12-slim, non-root user, alembic upgrade head + uvicorn |
| `frontend/Dockerfile` | node:20-alpine builder → nginx:alpine, non-root. PID fix: `sed pid /tmp/nginx.pid` |
| `frontend/nginx.conf` | SPA fallback + `/api/` proxy → backend:8000 |
| `backend/app/core/config.py` | pydantic-settings: AI_GATEWAY_URL/KEY/MODEL, DATABASE_URL, CORS |
| `backend/app/core/database.py` | async_engine, AsyncSessionLocal, get_db() dependency |
| `backend/app/models/protocol.py` | 5 таблиц: Protocol, ProtocolVersion, Template, OpenIssue, AuditLog |
| `backend/app/schemas/protocol.py` | Pydantic v2: Create/Update/Response + `error_body()` |
| `backend/app/schemas/generate.py` | GenerateRequest/Status, CheckResponse, GcpHint, DiffResponse (P2 stub) |
| `backend/app/services/ai_gateway.py` | AIGatewayClient: httpx + tenacity ×3. Только Qwen. HTTP 503 при сбое. |
| `backend/app/services/generator.py` | 12 секций, MVP=7, THERAPEUTIC_AREA/PHASE контексты, fallback |
| `backend/app/services/consistency.py` | GCP+RF check, JSON парсинг, fallback при недоступности |
| `backend/app/services/export_service.py` | MD ✅ HTML ✅ DOCX ✅ (P2, готов к включению) |
| `backend/app/routers/health.py` | GET /health |
| `backend/app/routers/protocols.py` | CRUDL + /versions + /diff stub → 501 |
| `backend/app/routers/generate.py` | POST /generate (async BackgroundTask) + GET status |
| `backend/app/routers/check.py` | POST /check → consistency + open_issues persist |
| `backend/app/routers/export.py` | GET /export?format=md\|html\|docx. `selectinload(open_issues)` — обязательно! |
| `backend/app/routers/templates.py` | GET /templates, POST stub → 501 |
| `backend/app/main.py` | FastAPI app, CORS, global error handler, lifespan |
| `backend/alembic/versions/001_initial_schema.py` | 5 таблиц + индексы + 3 seed templates (Phase I/II/III) |

**⚠️ Важно для export.py:** `selectinload(Protocol.open_issues)` обязателен иначе greenlet_spawn ошибка при экспорте.

**P2 готовность в коде:**
- DOCX: реализован в `export_service.py`, включить снятием `NotImplementedError`
- Diff: схемы готовы в `schemas/generate.py`, endpoint-stub в `protocols.py`
- SAP/ICF: добавить эндпоинты + секции в `generator.py`

---

### Фаза 1.5 — Swagger Verification ✅ 100% (завершена 23.04.2026)

Все P0 эндпоинты проверены через `curl`/`Invoke-RestMethod`:

| Эндпоинт | Статус |
|---|---|
| `GET /health` | ✅ `{"status":"ok","db":"connected"}` |
| `POST /api/v1/protocols` | ✅ 201 + UUID |
| `GET /api/v1/protocols` | ✅ 200 + список |
| `POST /api/v1/protocols/{id}/generate` | ✅ 202 + task_id |
| `GET /api/v1/protocols/{id}/generate/{task_id}` | ✅ completed 7/7 sections |
| `GET /api/v1/protocols/{id}/export?format=md` | ✅ 200 + файл 3838b |
| `GET /api/v1/protocols/{id}/export?format=html` | ✅ 200 + файл 5352b |
| `GET /api/v1/templates` | ✅ 200 + 3 шаблона |

---

### Фаза 2 — Frontend ✅ 100% (завершена 23.04.2026)

**Стек:** React 18 + Vite 6 + TypeScript + Tailwind CSS 3

| Файл | Описание |
|---|---|
| `frontend/package.json` | react 18.3, react-router-dom 6.27, react-markdown 9, lucide-react |
| `frontend/vite.config.ts` | Proxy `/api` → backend (port из `BACKEND_PORT` env var, default 50159) |
| `frontend/tailwind.config.js` | brand palette (sky 500/600/700) + custom components |
| `frontend/src/index.css` | Tailwind base + `btn-primary`, `btn-secondary`, `card`, `badge`, `form-input` |
| `frontend/src/App.tsx` | BrowserRouter: `/protocols`, `/protocols/new`, `/protocols/:id` |
| `frontend/src/api/client.ts` | Типизированный API клиент: все endpoint типы (Template, Protocol, GenerateStatus, CheckResponse) |
| `frontend/src/components/Layout.tsx` | Header + NavLink + footer ("FOR RESEARCH USE ONLY") |
| `frontend/src/components/StatusBadge.tsx` | draft/generating/generated/error — цвета + pulse |
| `frontend/src/components/Spinner.tsx` | SVG spinner |
| `frontend/src/components/ErrorAlert.tsx` | Алерт с закрытием |
| `frontend/src/pages/ProtocolListPage.tsx` | Список + Delete (с confirm) + EmptyState |
| `frontend/src/pages/CreateProtocolPage.tsx` | Форма: 5 секций, валидация, шаблоны, динамические критерии |
| `frontend/src/pages/ProtocolPage.tsx` | Viewer + Generate + polling + GCP panel + Export + Delete |

**Сборка:** `tsc + vite build` → 0 ошибок, 324kB JS + 18kB CSS

**⚠️ GenerateStatus расхождение API:** backend возвращает `sections_done: List[str]` и `sections_total: List[str]`, frontend ожидает числа. Polling работает через `.Count` / `.length`, но progress bar может показывать 0 пока не будет унифицирован формат. Исправить при Фазе 4 если нужно.

---

### Фаза 2.5 — QA Testing ✅ 100% (завершена 23.04.2026)

**Автотесты:** `pytest tests/ -v` → **31 passed, 0 failed, 0 errors** (14.84s)

```bash
# Запуск (нужно создать protocols_test БД один раз):
docker compose exec db psql -U app -d protocols -c "CREATE DATABASE protocols_test OWNER app;"
docker compose exec backend pytest tests/ -v
```

| Файл | Покрытие |
|---|---|
| `tests/conftest.py` | function-scoped fixtures, seed SQL, mock_ai_gateway_ok/fail, mock_consistency_ok |
| `tests/test_health.py` | 1 тест |
| `tests/test_protocols.py` | 20 тестов (CRUDL + 8 negative/ALT) |
| `tests/test_export.py` | 5 тестов (MD/HTML unit + 422 before-generate) |
| `tests/test_ai_gateway.py` | 5 тестов (retry, fallback, section count) |
| `tests/test_templates.py` | 4 теста (seed + 501-stub) |

**Ключевые исправления в тестах:**
- `conftest.py`: function-scoped async engine (pytest-asyncio 1.3 несовместим с session-scope)
- `conftest.py`: seed SQL вставляется после `create_all` (Alembic не запускается в тестах)
- `export.py`: `selectinload(Protocol.open_issues)` — обязателен для предотвращения `greenlet_spawn` ошибки
- Все assertions: `resp.json()["detail"]["error"]["code"]` (FastAPI оборачивает в `detail`)

**Ручные тесты:**

| Сценарий | Результат |
|---|---|
| HP-01: BCD-100 Phase II Create→Generate(7/7)→Export MD(3838b) HTML(5352b) | ✅ PASS |
| HP-02: BCD-089 Phase III Create→Generate start | ✅ PASS |
| ALT: 404, 422, 501 все правильные коды | ✅ PASS |

---

### Фаза 3 — Deploy 🔲 0% ← **СЛЕДУЮЩИЙ ШАГ**

**Что нужно сделать:**
1. Прочитать `dokploy-repo-prep/SKILL.md` — специфика Dokploy
2. Добавить Traefik labels в `docker-compose.yml`
3. Настроить Dokploy: New Project → Docker Compose → GitLab repo
4. Задать env vars в Dokploy UI (AI_GATEWAY_URL, AI_GATEWAY_API_KEY, POSTGRES_PASSWORD)
5. Deploy → получить публичный URL
6. Проверить `/health` и HP-01 на продакшен URL

**Ограничения docker-compose для Dokploy:**
- Без `container_name`
- Порты: short syntax `- "80"` (без `80:80`)
- Named volumes только (`db-data`, не `./data`)
- Non-root user + HEALTHCHECK — уже есть

---

### Фаза 4 — P1 Features 🔲 0%

- Версионирование UI (GET /versions в ProtocolPage уже есть)
- GCP Check UI (уже реализован в ProtocolPage — `GcpCheckPanel`)
- DOCX export (снять `NotImplementedError` в `export_service.py`)
- Унификация `GenerateStatus` (sections_done: list→number)

---

### Фаза 5 — P2 Features 🔲 0% (если останется время)

- SAP/ICF генерация — добавить промпты + эндпоинты
- Diff UI — схемы готовы, нужен frontend + диффер

---

## 6. Локальный запуск (воспроизведение среды)

```bash
# Полный стек в Docker
docker compose up -d
# Backend: http://localhost:<random_port>/docs
# Frontend: http://localhost:<random_port>/ (nginx)

# Vite dev server (рекомендуется для разработки)
cd frontend
$env:BACKEND_PORT = "50159"   # актуальный порт backend из docker compose ps
npm run dev
# → http://localhost:5174/

# Тесты
docker compose exec db psql -U app -d protocols -c "CREATE DATABASE protocols_test OWNER app;"  # один раз
docker compose exec backend pytest tests/ -v

# Проверка экспорта (после генерации)
$proto_id = "<uuid из POST /protocols>"
Invoke-WebRequest -Uri "http://localhost:50159/api/v1/protocols/$proto_id/export?format=md" -UseBasicParsing
```

---

## 7. Ключевые ограничения (нельзя менять)

### Архитектурные
1. **PostgreSQL** — финальный выбор, не SQLite
2. **AI Gateway** (единственный провайдер) → `InHouse/Qwen3.5-122B`, fallback на внешние LLM запрещён (NFR-08)
3. **Dokploy** — деплой-платформа (не Vercel, не Railway)
4. **GitLab** `gitlab.biocad.ru` — репозиторий (не GitHub)

### Docker/Dokploy (hard constraints)
5. **Без `container_name`** в docker-compose
6. **Порты short syntax** `- "80"` — без `80:80`
7. **Named volumes only** `db-data` — не `./` пути
8. **Non-root user** в Dockerfile — обязательно
9. **HEALTHCHECK** для каждого сервиса

### Качество кода
10. **English naming** — таблицы БД, колонки, Python-код, API endpoints
11. **snake_case** для всех JSON полей API
12. **ALCOA++ / SMART / CRUDL** — все документы и API

---

## 8. Демо-данные (синтетические, уже в БД)

**Протокол 1 — Фаза II, Онкология (BCD-100):**
- id: `f28eb6a3-ba04-4405-85f9-81ed24611378`
- Статус: generated (7/7 секций)
- Экспорт MD: 3838b, HTML: 5352b

**Протокол 2 — Фаза III, Дерматология (BCD-089):**
- id: `11639775-5884-495b-a657-f3cd4ec77135`
- Статус: generating (started)

**Seed шаблоны (3 шт):** Phase I FIH, Phase II Single-Arm, Phase III RCT

---

## 9. Структура файлов (актуальная)

```
c:\research-protocols-23042026\
├── CHECKPOINT.md            ← v3.0.0 (этот файл)
├── ARCHITECTURE.md          ← v1.2.0
├── README.md, DEPLOY.md, PROMPTS.md, RELEASE-NOTES.md
├── docker-compose.yml       ← 3 сервиса, named volumes, HEALTHCHECK
├── backend/
│   ├── Dockerfile           ← python:3.12-slim, non-root
│   ├── requirements.txt     ← fastapi, sqlalchemy, pytest-asyncio>=1.3
│   ├── pytest.ini           ← asyncio_mode=auto
│   ├── app/
│   │   ├── main.py
│   │   ├── core/config.py, database.py
│   │   ├── models/protocol.py   ← 5 таблиц
│   │   ├── schemas/protocol.py, generate.py
│   │   ├── services/ai_gateway.py, generator.py, consistency.py, export_service.py
│   │   └── routers/health.py, protocols.py, generate.py, check.py, export.py, templates.py
│   ├── alembic/
│   │   └── versions/001_initial_schema.py  ← 3 seed templates
│   └── tests/
│       ├── conftest.py      ← function-scoped fixtures + seed SQL
│       ├── test_health.py
│       ├── test_protocols.py
│       ├── test_export.py
│       ├── test_ai_gateway.py
│       └── test_templates.py
├── frontend/
│   ├── Dockerfile           ← node:20 builder → nginx:alpine, pid /tmp/nginx.pid fix
│   ├── nginx.conf           ← SPA + /api/ proxy
│   ├── package.json         ← react 18, vite 6, tailwind 3, react-markdown 9
│   ├── vite.config.ts       ← proxy: BACKEND_PORT env var (default 50159)
│   ├── tailwind.config.js
│   ├── tsconfig.app.json
│   ├── index.html
│   └── src/
│       ├── App.tsx           ← BrowserRouter + 3 routes
│       ├── index.css         ← Tailwind + custom classes
│       ├── api/client.ts     ← все типы + fetch wrappers
│       ├── components/Layout.tsx, StatusBadge.tsx, Spinner.tsx, ErrorAlert.tsx
│       └── pages/ProtocolListPage.tsx, CreateProtocolPage.tsx, ProtocolPage.tsx
├── docs/
│   ├── test-plan.md         ← v2.0.0 QA план
│   ├── api-spec.md          ← v1.2.0
│   └── [все прочие docs]
├── prompts/
│   ├── system-prompt.md
│   ├── section-generators/
│   └── validation-prompts/gcp-compliance.md, consistency-check.md
├── canvases/
│   ├── c4-architecture.canvas.tsx
│   └── protocol-generator-ui.canvas.tsx
└── dokploy-repo-prep/SKILL.md  ← обязательно читать перед деплоем!
```

---

## 10. GitLab

**Репозиторий:** `git@gitlab.biocad.ru:biocad/sandbox/hg-dis-group1-23042025/analysis-dudchenkoi-23042026.git`  
**Ветка:** `master`

**История коммитов (последние):**
```
492ac1e fix(frontend): nginx non-root pid path + vite proxy env-var port
dcd08ee fix(qa): Phase 2.5 - 31/31 tests pass, fix export selectinload
f8041d5 feat(frontend): Phase 2 - React + Vite + TS + Tailwind SPA
3614ed3 fix: SSL cert bypass for pip, CORS JSON format, protocol UUID pre-generation
99eadf1 chore: remove scaffold templates not related to project
a0b7e6f feat: initial project commit - AI Clinical Protocol Generator
```

---

## 11. Что делать первым при восстановлении контекста

1. Прочитать **этот файл** (CHECKPOINT.md) полностью
2. Проверить статус docker: `docker compose ps`
3. Если нужно продолжить разработку — запустить Vite: `cd frontend && $env:BACKEND_PORT="<port>" && npm run dev`
4. Следующая задача: **Фаза 3 — Deploy на Dokploy**
   - Прочитать `dokploy-repo-prep/SKILL.md`
   - Добавить Traefik labels в `docker-compose.yml`
   - Деплой через Dokploy UI с GitLab репо

---

## 12. Dokploy-специфика (из SKILL.md)

Скилл: `c:\research-protocols-23042026\dokploy-repo-prep\SKILL.md`

- AutoDeploy = `rm -rf` + `git clone` каждый раз → `./` volume paths ломаются
- `env -i` при деплое — только `.env` файл доходит до контейнера
- Домены = Traefik labels → обязателен редеплой после изменения домена
- Isolated Deployment рекомендован (Advanced → Enable)

---

## 13. Ключевые изменения по сессиям

### Сессия 1 (23.04.2026 — утро)
- Создан проект, документация (Фаза 0)
- Backend MVP + Docker Compose (Фаза 1)
- Исправления: SSL pip, CORS JSON, UUID pre-generation

### Сессия 2 (23.04.2026 — день)
- QA план, автотесты backend (conftest + 5 файлов тестов)
- Swagger verification (Фаза 1.5) — все P0 эндпоинты ✅
- Push в GitLab, очистка репо от scaffold файлов

### Сессия 3 (23.04.2026 — вечер)
- **Фаза 2 Frontend** — React SPA с 3 страницами, полным API клиентом, Tailwind UI
- **Фаза 2.5 QA** — 31/31 pytest, ручные HP-01/HP-02/ALT сценарии
- Исправления: pytest-asyncio 1.x fixtures, greenlet export bug, nginx pid non-root
- Локальный сервер: http://localhost:5174/ (Vite) + http://localhost:56403/ (Docker nginx)

### Сессия 4 (23.04.2026 — ночь) ← текущая
- **Auth/RBAC** — JWT (python-jose), PBKDF2 пароли, 3 роли (admin/employee/auditor)
  - `POST /api/v1/auth/token` — OAuth2 password flow
  - `GET /api/v1/auth/me` — whoami
  - Admin + Employee: read, create, update, delete
  - Auditor: read only (write → 403)
- **AuditLog** — `performed_by` (username) + role в metadata_ для всех actions (кто, где, когда, зачем)
- **Frontend** — LoginPage + AuthContext + ProtectedRoute + Layout (badge/logout)
- **Quick fixes:**
  - DOCX кнопка в UI (export: md/html/docx все три)
  - Watermark: `FOR DEMONSTRATION PURPOSES ONLY — SYNTHETIC DATA | AI-Assisted...`
  - Federal Registry КИ link в footer
  - `duration_ms` в AuditLog.metadata_ для ai_generate
- **FR-03.5** — Перегенерация отдельной секции: `POST /protocols/{id}/sections/{key}/regenerate`
- **FR-06.2** — Поле комментария к версии в UI
- **Тесты** — 42/42 passed: +11 auth тестов (login, RBAC, auditor read-only, JWT flow)
- **Backend deps:** добавлены `python-jose[cryptography]`, `python-multipart`; убрана passlib (заменена на hashlib PBKDF2)
