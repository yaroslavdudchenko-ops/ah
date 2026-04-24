# CHECKPOINT — Восстановление контекста

**Создан:** 2026-04-23  
**Версия:** 6.0.0  
**Обновлён:** 2026-04-23 (сессия 6 — Synthia branding, search, draft viewer, tag QA, docs)  
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
| База данных | PostgreSQL 16 (JSONB для секций и тегов, docker-compose сервис `db`) | ADR-001 |
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
AI_GATEWAY_URL=http://host.docker.internal:11434   # Ollama на хосте (не localhost!)
AI_GATEWAY_API_KEY=dev-key
AI_GATEWAY_MODEL=InHouse/Qwen3.5-122B
POSTGRES_USER=app
POSTGRES_PASSWORD=app_dev_password
POSTGRES_DB=protocols
DATABASE_URL=postgresql+asyncpg://app:app_dev_password@db:5432/protocols
CORS_ORIGINS=["http://localhost","http://localhost:80","http://localhost:8000"]
```

### Текущие порты (меняются при каждом restart!)
- **Frontend:** http://localhost:52698  
- **Backend API:** http://localhost:52697  
- **Backend Swagger:** http://localhost:52697/docs  
- **DB:** localhost:56014 (PostgreSQL)

### docker-compose.yml — важные нюансы

- `CORS_ORIGINS` передаётся как JSON-строка
- Порты меняются при каждом `docker compose restart` (random port mapping)
- `AI_GATEWAY_URL` должен быть `http://host.docker.internal:11434` (не localhost!) — иначе из Docker не достучаться до Ollama на хосте

---

## 5. Текущее состояние проекта

### Фаза 0 — Документация ✅ 100%

Все документы в `docs/`, включая `test-plan.md` v3.2.0, `api-spec.md` v1.5.0, `manual-test-guide.md` v1.0.0, `debug-guide.md` v1.0.0.

---

### Фаза 1 — Backend ✅ 100%

| Файл | Описание |
|---|---|
| `docker-compose.yml` | 3 сервиса: db, backend, frontend. Named volumes. HEALTHCHECK. |
| `backend/Dockerfile` | python:3.12-slim, non-root user, alembic upgrade head + uvicorn |
| `frontend/Dockerfile` | node:20-alpine builder → nginx:alpine, non-root. PID fix. |
| `frontend/nginx.conf` | SPA fallback + `/api/` proxy → backend:8000 |
| `backend/app/core/config.py` | pydantic-settings: AI_GATEWAY_URL/KEY/MODEL, DATABASE_URL, CORS |
| `backend/app/core/database.py` | async_engine, AsyncSessionLocal, get_db() dependency |
| `backend/app/models/protocol.py` | 5 таблиц: Protocol, ProtocolVersion, Template, OpenIssue, AuditLog |
| `backend/app/schemas/protocol.py` | Pydantic v2: Create/Update/Response + `error_body()` |
| `backend/app/services/ai_gateway.py` | AIGatewayClient: httpx + tenacity ×3. HTTP 503 при сбое. |
| `backend/app/services/generator.py` | 12 секций, MVP=7, THERAPEUTIC_AREA/PHASE контексты |
| `backend/app/services/consistency.py` | GCP+RF check, JSON парсинг, fallback. Обновлена нормативная база. |
| `backend/app/services/export_service.py` | MD ✅ HTML ✅ DOCX ✅ |
| `backend/app/routers/protocols.py` | CRUDL + search/filter + /versions + /diff stub |
| `backend/app/routers/generate.py` | POST /generate (async BackgroundTask) + GET status |
| `backend/app/routers/check.py` | POST /check → consistency + open_issues persist |
| `backend/app/routers/export.py` | GET /export?format=md\|html\|docx |
| `backend/app/routers/auth.py` | POST /auth/token (OAuth2) + GET /auth/me |
| `backend/app/routers/audit.py` | GET /audit-log (global) + GET /protocols/{id}/audit |

---

### Фаза 1.5 — Swagger Verification ✅ 100%

Все P0 эндпоинты верифицированы через curl/PowerShell.

---

### Фаза 2 — Frontend ✅ 100%

| Файл | Описание |
|---|---|
| `frontend/src/App.tsx` | BrowserRouter: routes для /protocols, /protocols/new, /protocols/:id, /audit |
| `frontend/src/api/client.ts` | Типизированный клиент: Protocol, ProtocolListItem (с therapeutic_area), AuditEntry, etc. |
| `frontend/src/components/Layout.tsx` | Synthia брендинг, NavLink, логотип-ссылка на /protocols |
| `frontend/src/components/SynthiaOrb.tsx` | SVG Morphing Blob анимация генерации |
| `frontend/src/components/DraftModal.tsx` | Модал полного просмотра черновика + print/PDF |
| `frontend/src/components/TagBadge.tsx` | Цветной тег-чип (hash-based color) |
| `frontend/src/pages/LoginPage.tsx` | Synthia логин, Sparkles icon, gradient |
| `frontend/src/pages/ProtocolListPage.tsx` | Список + поиск + автокомплит + фильтры (фаза/статус/область) + теги |
| `frontend/src/pages/CreateProtocolPage.tsx` | Форма создания с тегами (TagInput) |
| `frontend/src/pages/ProtocolPage.tsx` | Viewer + Generate (SynthiaOrb) + Draft viewer + GCP panel + Export + Audit tab |
| `frontend/src/pages/AuditTrailPage.tsx` | Глобальный журнал аудита + фильтр дат + PDF |

---

### Фаза 2.5 — QA Testing ✅ 100%

**Автотесты:** `pytest tests/ -v` → **136 passed, 0 failed**

| Файл | Тестов |
|---|---|
| `tests/test_health.py` | 1 |
| `tests/test_protocols.py` | 20 |
| `tests/test_export.py` | 5 |
| `tests/test_ai_gateway.py` | 5 |
| `tests/test_templates.py` | 4 |
| `tests/test_auth.py` | 11 |
| `tests/test_form_scenarios.py` | 50 |
| `tests/test_realistic_scenarios.py` | 40 |

**Ручные тесты:** test-plan.md v3.2.0 — добавлены TAG-01..05, SEARCH-01..02, DRAFT-01..02, UI-01

---

### Фаза 3 — Deploy 🔄 In Progress ← **ТЕКУЩИЙ ШАГ (24.04.2026)**

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

### Фаза 4 — P1 Features 🔲 Частично готово

- Версионирование UI ✅ (реализовано)
- GCP Check UI ✅ (реализовано)
- DOCX export ✅ (реализовано)
- Audit Trail ✅ (реализовано)
- Теги ✅ (реализовано)
- Поиск + фильтры ✅ (реализовано)
- Draft viewer ✅ (реализовано)
- SynthiaOrb анимация ✅ (реализовано)

---

### Фаза 5 — P2 Features 🔲 Backlog

- SAP/ICF генерация — добавить промпты + эндпоинты
- Diff UI — схемы готовы, нужен frontend + диффер

---

### Фаза 6 — P3 Интеграции и AI улучшения 🔲 Post-MVP Backlog

#### RAG (Retrieval-Augmented Generation) — Вариант 1: pgvector

**Решение принято:** pgvector в текущем PostgreSQL (смена образа `postgres:16` → `pgvector/pgvector:pg16`).

**Архитектура:**
```
Indexing:  ProtocolVersion.content[section] → EmbeddingService → protocol_embeddings(vector)
Retrieval: embed(title+indication+phase) → SELECT ... ORDER BY embedding <-> $1 LIMIT 3
Enhanced:  RAG context (top-3 похожих секций) → LLM prompt → лучший раздел
```

**Что нужно сделать при реализации:**
1. Уточнить у BIOCAD IT: работает ли текущий `AI_GATEWAY_API_KEY` для `https://aigateway.biocad.ru/api/v2/embeddings`?
2. Добавить `AI_EMBEDDING_URL=https://aigateway.biocad.ru/api/v2` и `AI_EMBEDDING_MODEL=InHouse/embeddings-model-1` в `.env` и `config.py`
3. Сменить образ в docker-compose: `pgvector/pgvector:pg16` (данные не теряются, нужен `pg_dumpall` если prod)
4. Alembic миграция: `CREATE EXTENSION vector` + таблица `protocol_embeddings`
5. Новый файл `backend/app/services/embedding_service.py`
6. Fallback: если similarity < 0.7 или найдено < 2 документов — генерировать без RAG
7. Индексация существующих протоколов (seeder при старте)
8. Mock embeddings в тестах

**Переходить на pgvector когда:** similarity-запросы > 100 мс ИЛИ корпус > 5000 протоколов.  
**До этого момента**: JSON-колонка + numpy cosine_similarity в Python (нулевые изменения инфраструктуры).

**Риски к моменту реализации:**
- "Холодный старт" — RAG даёт пользу при 20+ реальных протоколах в БД
- Проверить доступность `aigateway.biocad.ru` из Docker-контейнера Dokploy
- Legal/InfoSec согласование: встраивать только метаданные, не полные тексты секций

---

- **ct.biocad.ru ↔ Synthia** — Импорт реестра препаратов BIOCAD для автозаполнения формы.  
  **Статус:** Ожидает получения доступа к внутреннему API от BIOCAD IT.  
  **Решение:** Запросить у BIOCAD IT endpoint с реестром препаратов/исследований + условия подключения (JWT/OAuth).  
  **Риски зафиксированы:**
  - Отсутствие публичного API (нужен внутренний endpoint)
  - Регуляторные ограничения 61-ФЗ на публикацию данных КИ до одобрения Минздрава
  - Необходима Security review при смешивании internal/external периметров
  - Условия использования ct.biocad.ru запрещают web scraping
  **Рекомендуемый первый шаг:** письмо в IT/Legal BIOCAD: "Есть ли внутренний API реестра исследований и условия подключения?"

---

## 6. Нормативная база (актуальная, обновлена 23.04.2026)

Зафиксирована в `prompts/validation-prompts/gcp-compliance.md` v1.2.0 и `backend/app/services/consistency.py`:

| Документ | Статус | Применение |
|---|---|---|
| ICH E6 (R2) | ✅ Актуален | Международный стандарт GCP |
| GCP ЕАЭС (Решение Совета ЕЭК №79, ред. №63 от 01.08.2025) | ✅ Основной с 01.09.2024 | Заменил Приказ №200н |
| 61-ФЗ (гл. 7, ст. 38–44) | ✅ Актуален | Правовая основа КИ в РФ |
| Приказ Минздрава №353н от 26.05.2021 | ✅ Актуален | Информированное согласие |
| Приказ Минздрава №75н от 17.02.2025 | ✅ Актуален | Изменения в протокол КИ |
| Приказ Минздрава №708н от 23.12.2024 | ✅ Актуален | Реестр разрешений на КИ |
| Решение Совета ЕЭК №77 от 03.11.2016 | ✅ Актуален | GMP ЕАЭС (исследуемые препараты) |
| ГОСТ Р 52379-2005 | ✅ Актуален | Национальный стандарт GCP |
| 152-ФЗ | ✅ Актуален | Защита персональных данных |
| ~~Приказ №200н~~ | ❌ Утратил силу с 01.09.2024 | Удалён из промптов |
| ~~Приказ Минпромторга №916~~ | ❌ Заменён | Заменён Решением ЕЭК №77 |

---

## 7. Критерии GCP-скоров

**ICH E6(R2) Score (0-100)** — базируется на:
- Наличие обязательных 12 разделов ICH E6(R2)
- Корректность терминологии
- Логическая консистентность между разделами
- Соответствие принципам GCP (Appendix 6-8)

**РФ НМД Score (0-100)** — базируется на:
- Соответствие GCP ЕАЭС (Решение ЕЭК №79/63)
- Наличие требований 61-ФЗ (информированное согласие, страхование)
- Соответствие Приказам №353н, №75н, №708н

Оба скора рассчитываются промптом в `consistency.py` → `CONSISTENCY_SYSTEM_PROMPT`.

---

## 8. Auth/RBAC

| Роль | Create | Read | Update | Delete |
|---|---|---|---|---|
| admin | ✅ | ✅ | ✅ | ✅ |
| employee | ✅ | ✅ | ✅ | ❌ |
| auditor | ❌ | ✅ | ❌ | ❌ |

Demo users из `.env`:
```
ADMIN_USERNAME=admin / ADMIN_PASSWORD=admin123
EMPLOYEE_USERNAME=employee / EMPLOYEE_PASSWORD=emp123
AUDITOR_USERNAME=auditor / AUDITOR_PASSWORD=aud123
```

JWT flow: `POST /api/v1/auth/token` (OAuth2 password) → Bearer token → все запросы.

---

## 9. Ключевые особенности UI (актуальные)

- **Название системы:** Synthia (заменило "AI Protocol Generator")
- **Логотип:** Sparkles icon + gradient `#818cf8 → #c084fc → #22d3ee`, кликабелен → /protocols
- **Анимация генерации:** SynthiaOrb — SVG Morphing Blob (Variant B), 3 морфирующих пути, SMIL animations
- **Кнопка «Черновик»:** появляется после генерации, открывает DraftModal со всеми разделами + print
- **Поиск:** строка поиска с автокомплитом (debounce 250ms, ≥2 символа), Enter применяет
- **Фильтры:** Фаза / Статус / Терапевтическая область, счётчик активных, сброс одним кликом
- **Теги:** цветные чипы (hash-based), добавление через Enter/запятую, фильтрация кликом
- **Audit Trail:** отдельная страница /audit + вкладка в каждом протоколе + PDF с датой печати
- **Delete RBAC:** кнопка удаления скрыта для employee и auditor в UI

---

## 10. Локальный запуск

```powershell
# Полный стек в Docker
docker compose up -d

# Проверить порты
docker compose ps

# Тесты
docker compose exec db psql -U app -d protocols -c "CREATE DATABASE protocols_test OWNER app;"  # один раз
docker compose exec backend pytest tests/ -v

# Пересборка после изменений кода
docker compose build --no-cache frontend backend
docker compose up -d --force-recreate frontend backend
```

---

## 11. Ключевые ограничения (нельзя менять)

1. **PostgreSQL** — финальный выбор, не SQLite
2. **AI Gateway** → `InHouse/Qwen3.5-122B`, fallback на внешние LLM запрещён (NFR-08)
3. **Dokploy** — деплой-платформа (не Vercel, не Railway)
4. **GitLab** `gitlab.biocad.ru` — репозиторий
5. **Без `container_name`** в docker-compose
6. **Порты short syntax** `- "80"` — без `80:80`
7. **Named volumes only** `db-data`
8. **Non-root user** в Dockerfile
9. **HEALTHCHECK** для каждого сервиса
10. **`AI_GATEWAY_URL=http://host.docker.internal:11434`** — не localhost!

---

## 12. Структура файлов (актуальная)

```
c:\research-protocols-23042026\
├── CHECKPOINT.md            ← v6.0.0 (этот файл)
├── ARCHITECTURE.md          ← v1.2.0
├── README.md, DEPLOY.md, PROMPTS.md, RELEASE-NOTES.md
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/config.py, database.py, security.py
│   │   ├── models/protocol.py          ← 5 таблиц (Protocol.tags: JSONB)
│   │   ├── schemas/protocol.py, generate.py
│   │   ├── services/ai_gateway.py, generator.py, consistency.py, export_service.py
│   │   └── routers/
│   │       ├── health.py, protocols.py, generate.py, check.py
│   │       ├── export.py, templates.py, auth.py, audit.py
│   ├── alembic/versions/001_initial_schema.py
│   ├── scripts/seed_demo.py
│   └── tests/ (93 тестов)
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── api/client.ts               ← ProtocolListItem с therapeutic_area
│       ├── contexts/AuthContext.tsx
│       ├── components/
│       │   ├── Layout.tsx              ← Synthia logo → Link to /protocols
│       │   ├── SynthiaOrb.tsx          ← SVG Morphing Blob анимация
│       │   ├── DraftModal.tsx          ← полный просмотр черновика + print
│       │   ├── TagBadge.tsx, TagInput.tsx
│       │   ├── StatusBadge.tsx, Spinner.tsx, ErrorAlert.tsx, ProtectedRoute.tsx
│       └── pages/
│           ├── LoginPage.tsx
│           ├── ProtocolListPage.tsx    ← search + autocomplete + filters
│           ├── CreateProtocolPage.tsx
│           ├── ProtocolPage.tsx        ← Draft button + SynthiaOrb + Audit tab
│           └── AuditTrailPage.tsx
├── docs/
│   ├── test-plan.md         ← v3.1.0 (добавлены TAG/SEARCH/DRAFT/UI тесты)
│   ├── api-spec.md          ← v1.5.0 (задокументированы search/filter params)
│   ├── VERSIONS.md          ← обновлён
│   └── [все прочие docs]
├── prompts/
│   ├── system-prompt.md
│   ├── section-generators/
│   └── validation-prompts/
│       ├── gcp-compliance.md           ← v1.2.0 (обновлена нормативная база)
│       └── consistency-check.md
└── dokploy-repo-prep/SKILL.md  ← читать перед деплоем!
```

---

## 13. GitLab

**Репозиторий:** `git@gitlab.biocad.ru:biocad/sandbox/hg-dis-group1-23042025/analysis-dudchenkoi-23042026.git`  
**Ветка:** `master`

---

## 14. История сессий

### Сессия 1 (23.04.2026 — утро)
- Создан проект, документация (Фаза 0), Backend MVP + Docker Compose (Фаза 1)

### Сессия 2 (23.04.2026 — день)
- QA план, Swagger verification, push в GitLab

### Сессия 3 (23.04.2026 — вечер)
- Фаза 2 Frontend — React SPA, Tailwind UI
- Фаза 2.5 QA — 93/93 pytest

### Сессия 4 (23.04.2026 — ночь)
- Auth/RBAC (JWT, PBKDF2, 3 роли), AuditLog, LoginPage
- Demo data (seed_demo.py): 4 протокола, 5 препаратов, разные статусы

### Сессия 5 (23.04.2026)
- Audit Trail UI (страница /audit + вкладка в протоколе + PDF)
- RBAC UI fixes (скрытие корзины для employee/auditor)
- Теги: TagInput, TagBadge, фильтрация, сохранение в JSONB
- Synthia брендинг: SynthiaOrb анимация, переименование
- Нормативная база GCP: Приказ №200н → GCP ЕАЭС, добавлены №75н, №708н, ЕЭК №77

### Сессия 6 (23.04.2026) ← текущая
- **Logo → NavLink:** логотип Synthia кликабелен → возврат на /protocols
- **DraftModal:** кнопка «Черновик» → модал всех разделов + print/PDF с watermark
- **ProtocolListPage:** полная переработка — поиск + autocomplete (debounce 250ms) + фильтры (Фаза/Статус/Область) + счётчик активных фильтров
- **Backend search:** `GET /protocols` получил query params: `search`, `status`, `therapeutic_area` (ilike)
- **api/client.ts:** `ProtocolListItem` расширен полями `therapeutic_area`, `inn`, `created_at`
- **test-plan.md v3.1.0:** добавлены ручные тесты TAG-01..05, SEARCH-01..02, DRAFT-01..02, UI-01; регрессионный чеклист расширен
- **api-spec.md v1.5.0:** задокументированы все query params `GET /protocols`
- **P3 Backlog:** зафиксирована фича интеграции с ct.biocad.ru (ожидает доступа к BIOCAD IT API)

---

## 15. Что делать первым при восстановлении контекста

1. Прочитать **этот файл** (CHECKPOINT.md) полностью
2. Проверить статус docker: `docker compose ps`
3. Актуальные порты видны в выводе ps
4. **Следующая задача: Фаза 3 — Deploy на Dokploy**
   - Прочитать `dokploy-repo-prep/SKILL.md`
   - Добавить Traefik labels в `docker-compose.yml`
   - Деплой через Dokploy UI с GitLab репо

---

## 16. Dokploy-специфика

Скилл: `c:\research-protocols-23042026\dokploy-repo-prep\SKILL.md`

- AutoDeploy = `rm -rf` + `git clone` каждый раз → `./` volume paths ломаются
- `env -i` при деплое — только `.env` файл доходит до контейнера
- Домены = Traefik labels → обязателен редеплой после изменения домена
- Isolated Deployment рекомендован (Advanced → Enable)
