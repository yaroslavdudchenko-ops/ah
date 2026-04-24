# Release Notes — Synthia AI Protocol Generator

**Version:** 3.0.0 | **Date:** 2026-04-24 | **Status:** Active

---

## v1.0.0 — MVP Release «Synthia»

**Дата:** 2026-04-24  
**Тип:** Initial MVP Release  
**Статус:** Released (local) | Deploy: Pending (Dokploy)

### Функциональность

#### Управление протоколами (CRUDL)
- Создание протокола: фаза (I/II/III/IV), МНН, терапевтическая область, популяция, эндпоинты, дозирование, критерии включения/исключения
- Просмотр, редактирование (PATCH), архивирование (статусы: draft → in_review → approved → archived)
- Список протоколов с поиском по названию/препарату (autocomplete, debounce 250ms) и фильтрами по фазе/статусу/терапевтической области
- Тегирование: цветные чипы (hash-based color), добавление через Enter/запятую, фильтрация в списке, сохранение в JSONB

#### AI-генерация
- Автоматическая генерация 12 разделов протокола через внутренний AI Gateway (`InHouse/Qwen3.5-122B`)
- Section-by-section генерация с BackgroundTasks (async), polling статуса
- Повтор при ошибке Gateway (tenacity, ×3, exponential backoff)
- Перегенерация отдельной секции
- Анимация SynthiaOrb (SVG Morphing Blob) во время генерации
- Просмотр черновика — DraftModal со всеми секциями + print/PDF

#### Версионирование
- История версий протокола (ProtocolVersion)
- Diff между версиями (stub endpoint, UI pending)
- Комментарий к версии при генерации

#### Проверка консистентности (GCP Compliance)
- POST /check → AI-анализ всех секций
- Два скора: ICH E6(R2) Score и РФ НМД Score (0-100 каждый)
- Список открытых вопросов (OpenIssue) с категориями: terminology, logic, missing_section, gcp_violation
- Нормативная база: ICH E6(R2), GCP ЕАЭС (Решение ЕЭК №79/63), 61-ФЗ, Приказы №353н/75н/708н, Решение ЕЭК №77, ГОСТ Р 52379-2005, 152-ФЗ

#### Экспорт
- Markdown (`.md`)
- HTML (`.html`)
- DOCX (`.docx`) — python-docx + Jinja2 + mistune

#### Аутентификация и RBAC
- JWT OAuth2 (POST /auth/token), Bearer token на всех защищённых эндпоинтах
- 3 роли: admin (CRUD), employee (create/read/update), auditor (read only)
- Пароли: PBKDF2-HMAC-SHA256
- Demo users из env vars (ADMIN/EMPLOYEE/AUDITOR)

#### Журнал аудита
- AuditLog: entity_type, entity_id, action, performed_by, role, model, duration_ms, created_at
- Глобальный журнал /audit (страница /audit в UI) + per-protocol вкладка
- Фильтрация по дате, экспорт в PDF с датой печати
- RBAC UI: кнопка удаления скрыта для employee и auditor

### Техническая архитектура
- Backend: Python 3.12, FastAPI, SQLAlchemy 2 async, Alembic
- Frontend: React 18, Vite, TypeScript, Tailwind CSS
- DB: PostgreSQL 16 (JSONB для sections и tags)
- Deploy: Docker Compose (3 сервиса), Dokploy + Traefik

### Демо-данные (4 протокола)
- BCD-100 (Пролголимаб) — Фаза II, меланома, статус: in_review
- BCD-089 (IL-17A) — Фаза III, псориаз, статус: approved
- BCD-021 (Ритуксимаб-БК) — Фаза III, лимфома, статус: approved
- BCD-132 (Тоцилизумаб-БК) — Фаза I, ревматоидный артрит, статус: draft

### Тестирование
- **136 автоматических тестов** (pytest): unit, integration, smoke, RBAC, realistic scenarios
- Тест-план v3.2.0 (docs/test-plan.md)
- Ручное руководство для тестирования: docs/manual-test-guide.md
- Debug-гайд: docs/debug-guide.md

### Известные ограничения
- AI Gateway требует подключения к BIOCAD инфраструктуре (недоступен локально без VPN/Ollama)
- Compliance scores (ICH + РФ НМД) рассчитываются AI — не прошли клиническую валидацию
- RAG не реализован — запланирован после MVP (pgvector, Вариант 1)

---

## v1.1.0 — Protocol Governance & Artifacts Release

**Дата:** 2026-04-24  
**Тип:** Feature Release  
**Статус:** Released

### Новые функции

#### Управление протоколом (Governance)
- **4-eyes principle**: кнопка «Одобрить» недоступна создателю протокола (FR-09.1); HTTP 403 `SELF_APPROVAL_FORBIDDEN` + UI-дисклеймер
- **Блокировка генерации после одобрения**: generate и section_regen возвращают HTTP 423 `PROTOCOL_APPROVED` для approved протоколов
- **Кнопка «Копия»**: `POST /protocols/{id}/copy` дублирует любой протокол в новый черновик без архивации оригинала
- **Отслеживание создателя**: поле `created_by` в модели `Protocol` + Alembic миграция 004

#### AI-генерация
- **Custom prompt**: пользователь может добавить собственные клинические инструкции к стандартному промпту (`GenerateRequest.custom_prompt`)
- **Prompt injection guard** (`prompt_guard.py`): 18 regex-паттернов, санитация перед отправкой в Gateway; HTTP 422 `PROMPT_INJECTION_DETECTED` / `PROMPT_TOO_LONG`
- **SAP генерация (Appendix A)**: промпт для Statistical Analysis Plan (ITT/PP/Safety, гипотезы, power analysis, missing data handling)
- **ICF генерация (Appendix B)**: промпт для Informed Consent Form по 61-ФЗ, ICH E6 R2 §4.8, Приказу №353н

#### Версионирование и Diff
- **Diff UI реализован**: `GET /protocols/{id}/diff?v1=N&v2=N` использует `difflib.unified_diff`; цветная слайд-панель (зелёный/красный/синий) в ProtocolPage

#### Фильтры и UI
- **Статус «На ревью»** добавлен в фильтры списка протоколов (`in_review`)
- **Open Issues dropdown**: объединены кнопки «Скачать JSON» / «Скачать CSV» в один dropdown

#### Данные
- **BIOCAD API seeder**: `scripts/seed_from_biocad_api.py` — 15 протоколов из `api.biocadless.com` (разные терапевтические области и фазы)
- **`GET /api/v1/biocad-trials`**: proxy-эндпоинт публичного BIOCAD API с фильтрацией по area/phase

### Исправленные баги
- Повторяющийся текст в субтайтле протокола (truncate + title-атрибут для длинных drug_name/INN)

### Обновление документации
- `CHECKPOINT.md` v9.0.0
- `RELEASE-NOTES.md` v3.0.0
- `docs/functional-requirements.md` v1.3.0 (FR-05, FR-06, FR-09 обновлены)
- `docs/VERSIONS.md` v1.5.0
- `docs/artifacts-catalog.md` v1.3.0

---

## Backlog — v1.2.0 (Post-MVP)

### P3 Integrations
- RAG: pgvector в текущем PostgreSQL, `InHouse/embeddings-model-1`
- ct.biocad.ru интеграция: импорт реестра препаратов (ожидает API от BIOCAD IT)
- Уведомления рецензенту при переходе в `in_review`

---

## Формат записей

```markdown
## vX.Y.Z — Название релиза

**Дата:** YYYY-MM-DD
**Тип:** Feature Release | Bug Fix | Hotfix

### Новые функции
- ...

### Исправленные баги
- ...

### Breaking Changes
- ...
```
