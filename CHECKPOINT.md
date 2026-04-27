# CHECKPOINT — Восстановление контекста

**Создан:** 2026-04-23  
**Версия:** 14.0.0  
**Обновлён:** 2026-04-26 (сессия 14 — POST-DEADLINE: +5 парсинг BIOCAD, frontend polling fix, 37 протоколов в проде)  
**Назначение:** Полное восстановление контекста после очистки чата

> ⚠️ **POST-DEADLINE ИЗМЕНЕНИЯ** (после 2026-04-24 17:30):
> - `feat(seed)` коммит `5ed5464` (2026-04-26) — `seed_10_protocols.py`, `update_biocad_tags.py`, `PROJECT-SUMMARY.md`
> - `fix(login)` коммит `8769581` — исправлены демо-пароли (emp123, aud123)
> - `fix(ai-gateway)` коммит `168eeb5` — убран hardcoded /v1 prefix
> - `fix(frontend)` коммит `c387a84` — отмена устаревших запросов списка, `location.replace` на 401
> - `feat(seed)` коммит `a68cf57` (2026-04-26) — 5 реальных протоколов БИОКАД с парсингом `ct.biocad.ru`
> - **Продакшн (Dokploy):** 37 протоколов в БД (скрипт запущен через Dokploy Terminal)
> - Для отката к состоянию на дедлайн — см. раздел 17 ниже

---

## 0. Краткий summary (последняя сессия)

| Тема | Статус |
|------|--------|
| **Протоколы в проде** | **15 протоколов на сайте**. В БД ~37 записей суммарно (часть seed-скриптов запускалась только локально; не все данные попали в прод) |
| **Парсинг ct.biocad.ru** | 5 протоколов добавлены через `seed_biocad_5_protocols.py`: VERITAS, BCD-225-2, BCD-180-4, BCD-283-1, AQUARELLE. Реальные критерии включения/невключения, номера разрешений МЗ РФ/РБ. |
| **Frontend fix** | `ProtocolListPage`: убран `useCallback+useEffect([load])` → `useEffect([...deps])` с флагом отмены (`cancelled`). `api/client.ts`: `window.location.href` → `location.replace` на 401. |
| **Nginx polling** | Диагностировано: повторные запросы — Chrome speculative prefetch при наведении на `<Link>`. Не React-цикл. |
| **Git** | GitLab `origin` актуален: `a68cf57` (HEAD) |
| **⚠️ POST-DEADLINE** | Все изменения с `168eeb5` по `da2083f` сделаны ПОСЛЕ дедлайна 2026-04-24 17:30. Откат → раздел 17 |
| **Dokploy Terminal** | Работает через `/bin/sh` + `PYTHONPATH=/app /usr/local/bin/python3 <script>` |

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
| `backend/app/services/generator.py` | 14 секций (12 + SAP + ICF артефакты), MVP=7, THERAPEUTIC_AREA/PHASE контексты |
| `backend/app/services/consistency.py` | GCP+RF check, JSON парсинг, fallback. Обновлена нормативная база. |
| `backend/app/services/export_service.py` | MD ✅ HTML ✅ DOCX ✅ |
| `backend/app/routers/protocols.py` | CRUDL + search/filter + /versions + /diff (difflib) + /copy + /fork |
| `backend/app/routers/biocad_trials.py` | GET /biocad-trials — proxy BIOCAD публичного API |
| `backend/app/core/prompt_guard.py` | Санитация custom_prompt: 18 паттернов инъекций, max 2000 символов |
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

**Автотесты:** `pytest tests/ -v` → **137 passed, 0 failed**

| Файл | Тестов |
|---|---|
| `tests/test_health.py` | 1 |
| `tests/test_protocols.py` | 18 |
| `tests/test_export.py` | 5 |
| `tests/test_ai_gateway.py` | 5 |
| `tests/test_templates.py` | 4 |
| `tests/test_auth.py` | 12 |
| `tests/test_form_scenarios.py` | 51 |
| `tests/test_realistic_scenarios.py` | 41 |

**Ручные тесты:** test-plan.md v3.2.0 — добавлены TAG-01..05, SEARCH-01..02, DRAFT-01..02, UI-01

---

### Фаза 3 — Deploy 🔄 In Progress ← **ТЕКУЩИЙ ШАГ (24.04.2026)**

**Чеклист Dokploy пройден ✅** (проверен в сессии 11):
- ✅ No `container_name` в docker-compose.yml
- ✅ Порты: short syntax `- "80"`, `- "8000"`, `- "5432"`
- ✅ No `env_file`
- ✅ Обязательные env vars: `${VAR:?error}` синтаксис
- ✅ Non-root user (appuser) в обоих Dockerfile
- ✅ HEALTHCHECK в каждом сервисе
- ✅ Named volumes only (`db-data`)
- ✅ App слушает на `0.0.0.0`
- ✅ Traefik labels **НЕ нужны** — Dokploy инжектирует их сам через `addDomainToCompose`

**Что нужно сделать в Dokploy UI:**
1. Задать env vars в **Environment** (до Deploy):
   ```
   POSTGRES_PASSWORD=<openssl rand -hex 16>
   SECRET_KEY=<openssl rand -hex 32>
   AI_GATEWAY_URL=<URL внутреннего gateway>
   AI_GATEWAY_API_KEY=<ключ>
   DATABASE_URL=postgresql+asyncpg://app:<POSTGRES_PASSWORD>@db:5432/protocols
   CORS_ORIGINS=https://<your-domain>
   ```
2. Advanced → Enable Isolated Deployment
3. General → Deploy
4. Domains → Add Domain → Service: `frontend` → Port: `80` → Generate `*.traefik.me`
5. General → Deploy (повторный деплой после домена!)
6. Проверить `https://<domain>/health` → `{"status": "ok"}`

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

### Фаза 5 — P2 Features ✅ Реализовано

- SAP/ICF генерация ✅ — промпты (Appendix A & B) + кнопки в сайдбаре + хранятся в ProtocolVersion.content["sap"/"icf"]
- Diff UI ✅ — backend `GET /protocols/{id}/diff?v1=N&v2=N` (difflib.unified_diff) + слайд-панель в ProtocolPage
- Custom prompt + промпт-инъекция guard ✅ — `app/core/prompt_guard.py` (18 regex, HTTP 422)
- in_review в фильтрах ✅ — добавлен в STATUS_OPTIONS ProtocolListPage
- 4-eyes principle (одобрение) ✅ — creator не может approve собственный протокол (HTTP 403)
- Copy protocol ✅ — `POST /protocols/{id}/copy` дублирует черновик без архивации исходного
- created_by ✅ — поле в модели Protocol + миграция 004
- BIOCAD API seeder ✅ — `scripts/seed_from_biocad_api.py` + 15 протоколов из открытого API + `GET /api/v1/biocad-trials`

---

### Фаза 6 — P3 Интеграции и AI улучшения 🟡 В работе (RAG Phase 1)

#### RAG — реализовано (Phase 1, JSONB)

- Миграция **005**, таблица `protocol_embeddings`, векторы в JSONB + cosine в Python (`embedding_service.py`).
- API: `GET/POST /api/v1/embeddings/status`, `reindex`, и связанные эндпоинты; встраивание контекста в промпт генерации.
- Отдельный хардкод `aigateway.biocad.ru/api/v2/embeddings` и `verify=False` **сняты** (revert); эмбеддинги идут через настройки gateway (`AI_GATEWAY_URL` / ключ), как и чат.

#### RAG — следующий шаг (pgvector, backlog)

**Решение на будущее:** при росте корпуса — образ `pgvector/pgvector:pg16` + `CREATE EXTENSION vector` + колонка `vector` + IVFFlat/HNSW.

**Переходить на pgvector когда:** similarity в Python > 100 мс ИЛИ корпус > 5000 протоколов.

**Риски:**
- "Холодный старт" — RAG даёт пользу при 20+ реальных протоколах в БД
- Legal/InfoSec: в промпт попадают только согласованные фрагменты/метаданные

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
- **4-eyes approve:** кнопка «Одобрить» скрыта для creator протокола; дисклеймер при попытке самоодобрения
- **Diff panel:** «Сравнить версии» в сайдбаре (≥2 версий) → слайд-панель с unified diff по секциям
- **SAP/ICF:** раздел «Артефакты» в сайдбаре (Appendix A: SAP, Appendix B: ICF), кнопки генерации/просмотра
- **Custom prompt:** расширяемый блок «Настроить промпт для AI» в форме комментария
- **Prompt guard:** клиент получает 422 с понятным сообщением при попытке инъекции
- **in_review:** статус «На ревью» доступен в фильтрах списка протоколов

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
│   ├── alembic/versions/001..005_*.py
│   ├── scripts/
│   │   ├── seed_demo.py               ← исходные демо-данные
│   │   ├── seed_10_protocols.py       ← 10 синтетических протоколов (POST-DEADLINE)
│   │   ├── seed_from_biocad_api.py    ← 15 протоколов из api.biocadless.com
│   │   ├── update_biocad_tags.py      ← обновление тегов + BCD-281-2/MUSCAT (POST-DEADLINE)
│   │   └── seed_biocad_5_protocols.py ← 5 реальных протоколов с ct.biocad.ru (POST-DEADLINE)
│   └── tests/ (137 тестов)
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

### Сессия 14 (26.04.2026) ← текущая

- **+5 реальных протоколов BIOCAD**: `seed_biocad_5_protocols.py` — данные с `ct.biocad.ru/nozology/<slug>` (реальные критерии вкл/невкл, разрешения МЗ РФ/РБ, синтетические разделы дизайна/эндпоинтов). **37 протоколов в прод-БД.**
- **Диагностика Nginx polling**: определён Chrome speculative prefetch как источник повторных GET /api/v1/protocols в логах (не React-цикл).
- **fix(frontend)**: `ProtocolListPage.tsx` — рефакторинг `useEffect` с флагом `cancelled` (устранение race condition); `api/client.ts` — `location.replace('/login')` вместо `href` при 401.
- **Dokploy Terminal debug**: разрешены bash/python/PYTHONPATH проблемы; команда для выполнения: `PYTHONPATH=/app /usr/local/bin/python3 /app/scripts/<script>.py`
- **CHECKPOINT** v14.0.0

### Сессия 13 (26.04.2026)

- **BIOCAD protocols patch**: `update_biocad_tags.py` — обновлены теги у 15 BIOCAD-протоколов ("Набор открыт"/"Набор завершен"), добавлен `BCD-281-2/MUSCAT`. **32 протокола в БД**.
- **Lokальный сервер**: пересборка образов после комита `8769581` (исправлены пароли emp123/aud123). Логин через UI — работает.
- **CHECKPOINT** v13.0.0

### Сессия 11 (24.04.2026)

- **Проверка целостности**: После разрыва auto-сессии — git чистый, последний коммит `9a99d7f` (137 tests passed)
- **Dokploy чеклист**: Все правила соблюдены (no container_name, short ports, named volumes, non-root, healthcheck, no env_file)
- **Traefik labels**: Подтверждено — НЕ нужны в compose, Dokploy инжектирует сам
- **Push в GitLab**: Зафиксированы doc-изменения
- **CHECKPOINT** v11.0.0

### Сессия 10 (24.04.2026)

- **RAG Phase 1**: embeddings в БД (JSONB), сервис эмбеддингов, эндпоинты v1, интеграция в генерацию
- **Revert**: убрана привязка к BIOCAD-only URL эмбеддингов и небезопасный TLS; функциональность RAG сохранена
- **Тесты**: 137 passed — auth из env, diff (404 + два `ProtocolVersion` в той же БД что тест), lifecycle без одобрения создателем
- **GitHub**: push на `yaroslavdudchenko-ops/ah` (`9a99d7f` и связанные коммиты)
- **CHECKPOINT** v10.0.0

### Сессия 9 (24.04.2026)

- **Diff UI**: backend `GET /protocols/{id}/diff?v1=N&v2=N` (difflib.unified_diff) + слайд-панель сравнения в ProtocolPage (color-coded, секция по секции)
- **SAP/ICF генерация**: промпты Appendix A (SAP) и Appendix B (ICF), кнопки «Сгенерировать» в сайдбаре, хранение в ProtocolVersion.content
- **Prompt injection guard**: `backend/app/core/prompt_guard.py` — 18 regex-паттернов, HTTP 422 PROMPT_INJECTION_DETECTED + PROMPT_TOO_LONG
- **in_review фильтр**: добавлен в STATUS_OPTIONS на ProtocolListPage
- **Документация**: CHECKPOINT v9.0.0, RELEASE-NOTES v1.1.0, functional-requirements v1.3.0, VERSIONS v1.5.0, artifacts-catalog v1.3.0
- **Final Project Review canvas** обновлён с актуальными данными

### Сессия 8 (24.04.2026)

- **4-eyes principle**: creator не может approve свой протокол (HTTP 403 SELF_APPROVAL_FORBIDDEN); UI дисклеймер
- **Кнопка «Копия»**: `POST /protocols/{id}/copy` дублирует протокол в статус draft без архивации исходного
- **Custom prompt**: поле для кастомных инструкций AI, передаётся в `GenerateRequest.custom_prompt`
- **Блокировка генерации после approve**: HTTP 423 PROTOCOL_APPROVED для generate и section_regen
- **created_by**: поле в модели Protocol + Alembic миграция 004
- **BIOCAD API seeder**: `scripts/seed_from_biocad_api.py` — 15 протоколов из `api.biocadless.com`, `GET /api/v1/biocad-trials`
- **UI Open Issues dropdown**: «Открытые вопросы» → Скачать JSON / Скачать CSV (dropdown с иконками)

### Сессия 7 (24.04.2026)

- **GitLab push**: SSH ключ работает — все коммиты запушены (`master`)
- **Traefik labels**: добавлены в `docker-compose.yml` для frontend
- **`.env`**: дополнен всеми AUTH-переменными (ADMIN/EMPLOYEE/AUDITOR + SECRET_KEY + APP_DOMAIN)
- **Аудит документации GitLab**: найдено и исправлено 7 проблем:
  - `RELEASE-NOTES.md` переписан → v2.0.0 (отражает реальный MVP)
  - `ADR-002-openrouter.md` → `ADR-002-ai-gateway.md` (переименован)
  - `CHECKPOINT.md` обновлён (136 тестов, test-plan 3.2.0)
  - `smoke_test.http` — добавлены Bearer token заголовки
  - `.gitignore` — добавлен паттерн `qa_*.txt`
  - `design-system-plan.md` — обновлён статус и фактические компоненты
  - `artifacts-catalog.md` — ссылка на ADR-002 обновлена
- **backend/Dockerfile**: улучшен до multi-stage + добавлен HEALTHCHECK
- **`requirements-dev.txt`**: создан (pytest зависимости отдельно)
- **`docs/METRICS.md`**: создан — все метрики проекта для презентации заказчику
- **System Review canvas**: оценка 7.3/10, вердикт: Continue
- **WakaTime canvas**: 3ч 05мин трекера, 85% готовность, буфер 3.5ч до дедлайна
- **Фаза 3 (Deploy)**: ожидает URL Dokploy от пользователя

### Сессия 6 (23.04.2026)
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
   - Traefik labels уже добавлены в `docker-compose.yml` ✅
   - GitLab push работает по SSH ✅
   - Нужен URL Dokploy UI от пользователя
   - Инструкция: `DEPLOY.md` секция 6

**Для презентации заказчику:** `docs/METRICS.md` — все метрики проекта

---

## 16. Dokploy-специфика

Скилл: `c:\research-protocols-23042026\dokploy-repo-prep\SKILL.md`

- AutoDeploy = `rm -rf` + `git clone` каждый раз → `./` volume paths ломаются
- `env -i` при деплое — только `.env` файл доходит до контейнера
- Домены = Traefik labels → обязателен редеплой после изменения домена
- Isolated Deployment рекомендован (Advanced → Enable)

---

## 17. Откат прода (rollback)

> Актуально если нужно вернуться к состоянию на **дедлайн 2026-04-24 17:30**

### Состояние на дедлайн
- Последний коммит до дедлайна: `b80014d` (`feat(session-12)`, 2026-04-24 16:44)
- После дедлайна добавлены: `168eeb5`, `8769581`, `5ed5464`

### Коммиты ПОСЛЕ дедлайна (хронологически)

| Хэш | Дата | Описание |
|-----|------|----------|
| `168eeb5` | 2026-04-24 17:00 | fix(ai-gateway): remove hardcoded /v1 prefix |
| `8769581` | 2026-04-24 17:18 | fix(login): correct demo passwords (emp123, aud123) |
| `5ed5464` | 2026-04-26 19:29 | feat(seed): seed scripts, BIOCAD protocols patch, PROJECT-SUMMARY.md |
| `c387a84` | 2026-04-26 | fix(frontend): cancel stale list requests; use location.replace on 401 |
| `a68cf57` | 2026-04-26 | **feat(seed)**: 5 реальных протоколов BIOCAD с парсингом ct.biocad.ru |

### Инструкция по откату в Dokploy

**Вариант A — откат через Dokploy UI (рекомендован):**
1. Открыть Dokploy → вкладка **Deployments**
2. Найти деплой, соответствующий коммиту `b80014d` (дата ~16:44 24.04.2026)
3. Нажать **Redeploy** на нём — Dokploy задеплоит именно тот коммит

**Вариант B — откат через Git:**
```bash
# Создать rollback-ветку на дедлайн-коммите
git checkout -b rollback/deadline b80014d
git push origin rollback/deadline

# В Dokploy: сменить Branch на rollback/deadline → Deploy
```

**Вариант C — откат данных БД (только протоколы):**
Если нужно убрать только POST-DEADLINE протоколы из БД (не трогая код):
```bash
# В терминале Dokploy → backend
docker compose exec -e PYTHONPATH=/app backend python -c "
import asyncio
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.protocol import Protocol

# Удалить протоколы, добавленные системой (скриптами) после дедлайна
# Это: BCD-281-2/MUSCAT (единственный новый из update_biocad_tags.py)
async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    Session = async_sessionmaker(engine)
    async with Session() as db:
        result = await db.execute(
            select(Protocol).where(
                Protocol.drug_name == 'BCD-281-2/MUSCAT',
                Protocol.created_by == 'system'
            )
        )
        p = result.scalar_one_or_none()
        if p:
            await db.delete(p)
            await db.commit()
            print('Deleted BCD-281-2/MUSCAT')
        else:
            print('Not found')
    await engine.dispose()
asyncio.run(main())
"
```

### Что изменилось в данных после дедлайна
- **Добавлен 1 новый протокол:** `BCD-281-2/MUSCAT` (neurology, Набор открыт, created_by=system) — сессия 13
- **Обновлены теги** у 15 BIOCAD-протоколов: добавлены "Набор открыт" / "Набор завершен" — сессия 13
- **Добавлено 5 протоколов** из `seed_biocad_5_protocols.py` (VERITAS, BCD-225-2, BCD-180-4, BCD-283-1, AQUARELLE) — сессия 14
- **Итого протоколов на дедлайн:** 31 → **сессия 13:** 32 → **сессия 14 (прод):** 37
- Теги можно убрать вручную через UI; протоколы можно удалить через DELETE /api/v1/protocols/{id} (admin)

### Rollback данных (откат seed_biocad_5_protocols)
Для удаления 5 BIOCAD-протоколов сессии 14 через Dokploy Terminal (`/bin/sh`):
```
PYTHONPATH=/app /usr/local/bin/python3 -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import delete
from app.core.config import settings
from app.models.protocol import Protocol

TO_DELETE = ['BCD-267-2/VERITAS', 'BCD-225-2', 'BCD-180-4', 'BCD-283-1', 'BCD-132-6/AQUARELLE']

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    Session = async_sessionmaker(engine)
    async with Session() as db:
        for name in TO_DELETE:
            r = await db.execute(delete(Protocol).where(Protocol.drug_name == name))
            print(f'Deleted {r.rowcount} row(s): {name}')
        await db.commit()
    await engine.dispose()

asyncio.run(main())
"
```
