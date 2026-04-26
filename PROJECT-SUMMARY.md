# AI-генератор протоколов клинических исследований

**MVP · FastAPI + React · Dokploy · InHouse/Qwen3.5-122B**  
**Дедлайн:** 24.04.2026 17:30 · **Коммит:** `8769581` · **Тестов:** 137 passed

---

## Что делает система

Генерирует полные черновики протоколов клинических исследований на основе параметров препарата и терапевтической области. Соответствует **GCP ICH E6(R2), GCP ЕАЭС, 61-ФЗ**.

| Этап | Описание |
|---|---|
| **Ввод параметров** | Препарат, МНН, фаза I–III, показание, популяция, эндпоинты, критерии включения/исключения |
| **AI-генерация** | 12 секций + SAP + ICF через внутренний AI Gateway. Fallback при недоступности |
| **Экспорт и аудит** | MD / HTML / DOCX / открытые вопросы CSV. Каждое действие в audit log |

---

## Метрики

| Показатель | Значение |
|---|---|
| Тестов passed | **137** |
| Разделов протокола | **12 + SAP + ICF** |
| Роли пользователей | **3** (admin / employee / auditor) |
| Форматов экспорта | **4** (MD, HTML, DOCX, CSV) |
| Время разработки | **1.5 дня** |

---

## Технический стек

### Backend
| Компонент | Решение |
|---|---|
| API | FastAPI + Python 3.12 |
| ORM | SQLAlchemy async + asyncpg |
| Миграции | Alembic |
| БД | PostgreSQL 16 |
| LLM | InHouse/Qwen3.5-122B (AI Gateway `https://aigateway.biocad.ru/api/v2`) |
| Тесты | pytest-asyncio, httpx, 137 passed |
| Безопасность | JWT (python-jose), RBAC, prompt_guard, audit log |

### Frontend
| Компонент | Решение |
|---|---|
| Framework | React 18 + TypeScript |
| Сборка | Vite |
| Стили | Tailwind CSS |
| Роутинг | React Router |
| Сервер | nginx:alpine |

### Инфраструктура
| Компонент | Решение |
|---|---|
| Оркестрация | Docker Compose (3 сервиса) |
| Деплой | Dokploy (Docker Compose mode) |
| Reverse proxy | Traefik (инжектируется Dokploy) |
| VCS | GitLab (origin) + GitHub (mirror) |

---

## Ключевые функции

- **Генерация протокола** — Фазы I–III, 12 секций + Appendix SAP/ICF. Section-level перегенерация отдельных разделов
- **Intelligent Fallback** — при недоступном AI Gateway каждый раздел получает уникальный шаблон с реальными данными протокола (название препарата, показание, критерии)
- **Версионирование** — история версий с diff-сравнением, архивирование старых версий
- **GCP-проверка** — автоматическая consistency-проверка, открытые вопросы по типам (terminology, dosing, regulatory, missing_data)
- **RBAC** — admin / employee / auditor. Read-only для аудитора, write-lock для approved-протоколов
- **Audit log** — каждое действие (create, update, generate, export, check) логируется в БД (ALCOA++)
- **Экспорт** — Markdown, HTML, DOCX (python-docx). Открытые вопросы в JSON/CSV
- **Редактирование метаданных** — inline-редактирование параметров протокола после создания
- **Поиск и теги** — полнотекстовый поиск, фильтры по фазе/статусу/области, цветные теги

---

## Соответствие требованиям

| Требование | Статус |
|---|---|
| GCP ICH E6(R2) | ✅ |
| GCP ЕАЭС (решение ЕЭК №79) | ✅ |
| 61-ФЗ «Об обращении ЛС» | ✅ |
| ALCOA++ (audit trail) | ✅ |
| NFR-08 — только внутренний LLM | ✅ |
| RBAC 3 роли | ✅ |
| Dokploy hard constraints | ✅ |

---

## Архитектура (C4 — Container)

```
[Пользователь] → [Traefik] → [frontend: nginx:80]
                                    ↓ /api/*
                             [backend: FastAPI:8000]
                                    ↓
                             [db: PostgreSQL:5432]

backend → [AI Gateway: aigateway.biocad.ru/api/v2]
          (fallback: section-specific templates при ошибке)
```

### Ключевые таблицы БД

| Таблица | Назначение |
|---|---|
| `templates` | Шаблоны по фазам (I/II/III) |
| `protocols` | Метаданные протокола (phase, drug, indication, ...) |
| `protocol_versions` | Снапшоты сгенерированного контента (JSONB) |
| `open_issues` | GCP-замечания по версиям |
| `audit_log` | Immutable лог всех действий |
| `terminology` | Нормализация МНН и названий |
| `protocol_embeddings` | _(P3/RAG)_ Векторные индексы (pgvector) |

---

## История разработки

| Сессия | Ключевые результаты |
|---|---|
| 1–4 | Архитектура, БД-схема, базовый FastAPI + auth, Alembic миграции |
| 5–7 | AI Gateway интеграция, генератор 12 секций, prompt engineering |
| 8–9 | React UI: создание, просмотр, diff, аудит, экспорт, drag-and-drop теги |
| 10 | RAG Phase 1 (embeddings), 137 тестов, первый Dokploy-деплой |
| 11 | Фикс fallback-секций, edit-meta UI, отображение exclusion_criteria |
| 12 | SAP/ICF fallbacks, Phase IV удалена, export audit log, AI Gateway endpoint fix, фикс паролей демо-пользователей |

---

## Деплой (Production)

**URL:** `http://hgdisgroup123042025-analysisdudchenkoi23-05fc54-10-226-76-173.traefik.me`

| Сервис | Статус |
|---|---|
| frontend | healthy |
| backend | healthy |
| db | healthy |

### Учётные записи

| Логин | Пароль | Роль |
|---|---|---|
| `admin` | `admin123` | Полный доступ |
| `employee` | `emp123` | Создание и генерация |
| `auditor` | `aud123` | Только чтение |

### Переменные окружения (Dokploy)

```
AI_GATEWAY_URL=https://aigateway.biocad.ru/api/v2
AI_GATEWAY_API_KEY=<ключ>
AI_GATEWAY_MODEL=InHouse/Qwen3.5-122B
DATABASE_URL=postgresql+asyncpg://app:<pass>@db:5432/protocols
POSTGRES_PASSWORD=<pass>
```

---

## Swagger / API

**Docs:** `<base_url>/api/v1/docs`

Ключевые эндпоинты:

```
POST   /api/v1/auth/token                          — авторизация
GET    /api/v1/protocols                           — список протоколов
POST   /api/v1/protocols                           — создать протокол
PATCH  /api/v1/protocols/{id}                      — обновить метаданные
POST   /api/v1/protocols/{id}/generate             — запустить генерацию
GET    /api/v1/protocols/{id}/generate/{task_id}   — статус генерации
POST   /api/v1/protocols/{id}/sections/{s}/regenerate — перегенерировать секцию
GET    /api/v1/protocols/{id}/versions             — история версий
GET    /api/v1/protocols/{id}/export?format=md|html|docx
GET    /api/v1/protocols/{id}/audit                — audit log
POST   /api/v1/protocols/{id}/check                — GCP-проверка
GET    /health                                     — healthcheck
```

---

## Репозиторий

**GitLab:** `gitlab.biocad.ru/biocad/sandbox/hg-dis-group1-23042025/analysis-dudchenkoi-23042026`  
**Ветка:** `master`  
**Последний коммит:** `8769581` — fix(login): correct demo passwords
