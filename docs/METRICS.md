# Synthia — Project Metrics

**Версия:** 1.0.0 | **Дата:** 2026-04-24 | **Дедлайн:** 2026-04-24 17:30

Все метрики зафиксированы для презентации заказчику.

---

## 1. Время разработки (WakaTime)

| Дата | Время в проекте | Примечание |
|---|---|---|
| 23.04.2026 | 21 мин | Старт, документация |
| 24.04.2026 | 2ч 44мин | Финальная сессия |
| **Итого** | **~3ч 05мин** | Чистое время кодинга (WakaTime) |

**Редактор:** Cursor (100% — AI Coding category)  
**Распределение времени (24.04):**

| Язык | Время | % |
|---|---|---|
| TypeScript | 54 мин | 33% |
| Markdown | 39 мин | 24% |
| Other (YAML, conf) | 30 мин | 18% |
| Python | 24 мин | 15% |
| Bash | 11 мин | 7% |
| HTML/CSS/JSON | ~2 мин | 1% |

---

## 2. Кодовая база

| Категория | Файлов | Примечание |
|---|---|---|
| **Итого в репозитории** | **144** | Git HEAD |
| Backend (app/) | 27 | FastAPI routers, models, services, schemas |
| Frontend (src/) | 19 | Pages, components, contexts, API client |
| Tests | 11 | pytest файлов |
| Documentation (docs/) | 24 | MD-артефакты |
| Prompts | 4 | system-prompt + section-generators + validation |
| Config/Deploy | 6 | docker-compose, Dockerfiles, nginx.conf, .env.example |
| Root docs | 8 | README, ARCHITECTURE, CHECKPOINT, DEPLOY, PROMPTS, RELEASE-NOTES, CHECKPOINT, corecase |

**Изменения в последней сессии:** 64 файла, +6 722 строки добавлено, -809 удалено

---

## 3. Git активность

| Метрика | Значение |
|---|---|
| Коммитов (проект, с 23.04) | **16** |
| Первый коммит | 2026-04-23 20:40 |
| Последний коммит | 2026-04-24 (сессия 7) |
| Ветка | master |
| Репозиторий | gitlab.biocad.ru/biocad/sandbox/hg-dis-group1-23042025/analysis-dudchenkoi-23042026 |

**Коммиты по типам:**

| Тип | Количество |
|---|---|
| `feat` | 6 |
| `fix` | 5 |
| `docs` | 4 |
| `chore` | 1 |

---

## 4. Тестирование

| Метрика | Значение |
|---|---|
| **Автотестов всего** | **136** |
| Тест-файлов | 8 |
| Покрытие типов | unit, integration, smoke, RBAC, lifecycle, realistic scenarios |
| Результат последнего запуска | **136 passed, 0 failed** |

**Распределение тестов:**

| Файл | Тестов | Покрытие |
|---|---|---|
| `test_health.py` | 1 | Health endpoint |
| `test_protocols.py` | 20 | CRUDL API |
| `test_export.py` | 5 | MD/HTML/DOCX export |
| `test_ai_gateway.py` | 5 | AI Gateway client mock |
| `test_templates.py` | 4 | Templates API |
| `test_auth.py` | 11 | JWT + RBAC |
| `test_form_scenarios.py` | 50 | Форм-сценарии, валидация, негативные тесты |
| `test_realistic_scenarios.py` | 40 | Реалистичные данные BIOCAD |

**Ручные тесты:** test-plan v3.2.0 — 30+ сценариев (TAG, SEARCH, DRAFT, RBAC, LIFECYCLE, NEGATIVE)

---

## 5. API Endpoints

| Router | Endpoints | Методы |
|---|---|---|
| Health | 1 | GET /health |
| Auth | 2 | POST /auth/token, GET /auth/me |
| Protocols | 6 | GET list, POST create, GET detail, PATCH update, DELETE, GET versions |
| Generate | 2 | POST /generate, GET /generate/{task_id} |
| Check | 1 | POST /check (GCP consistency) |
| Export | 1 | GET /export?format=md\|html\|docx |
| Templates | 2 | GET list, GET detail |
| Audit | 2 | GET /audit-log (global), GET /protocols/{id}/audit |
| **Итого** | **17** | |

**Параметры поиска/фильтрации GET /protocols:**
`search`, `status`, `therapeutic_area`, `phase` (все query params, ilike)

---

## 6. Функциональность (Feature Coverage)

### Реализованные P0 (обязательные)

| Функция | Статус |
|---|---|
| Создание/просмотр/редактирование протоколов | ✅ |
| AI-генерация 12 разделов (async BackgroundTasks) | ✅ |
| Версионирование протоколов | ✅ |
| GCP/ICH E6(R2) + РФ НМД Compliance Check | ✅ |
| Экспорт MD / HTML / DOCX | ✅ |
| JWT Auth + RBAC (admin / employee / auditor) | ✅ |
| Audit Trail (кто, где, когда, сколько) | ✅ |
| Поиск по названию/препарату (autocomplete) | ✅ |
| Фильтры (фаза / статус / терапевтическая область) | ✅ |
| Теги (цветные чипы, фильтрация, JSONB) | ✅ |
| Draft Modal (просмотр + print/PDF) | ✅ |
| SynthiaOrb анимация генерации (SVG SMIL) | ✅ |
| Synthia брендинг (логотип → NavLink) | ✅ |
| Delete RBAC (скрыт для employee/auditor) | ✅ |
| Демо-данные (4 протокола, 2 препарата) | ✅ |
| Docker Compose (3 сервиса, healthchecks) | ✅ |
| Multi-stage Dockerfile + non-root | ✅ |
| Traefik labels для Dokploy | ✅ |

### P1 (реализованные бонусные)

| Функция | Статус |
|---|---|
| Audit Trail UI страница + per-protocol вкладка | ✅ |
| PDF экспорт журнала аудита с датой | ✅ |
| Фильтр по дате в журнале аудита | ✅ |
| Перегенерация отдельной секции | ✅ |
| Watermark "FOR REVIEW ONLY" | ✅ |

### Backlog (Post-MVP)

| Функция | Статус |
|---|---|
| Diff UI (схема готова, stub endpoint) | P2 |
| SAP / ICF генерация | P2 |
| RAG с pgvector | P3 (решение принято: pgvector) |
| ct.biocad.ru интеграция | P3 (ожидает API от BIOCAD IT) |

---

## 7. Архитектура

| Слой | Технология | Версия |
|---|---|---|
| Backend | Python + FastAPI | 3.12 / 0.111+ |
| ORM | SQLAlchemy async | 2.0 |
| Migrations | Alembic | 1.13+ |
| Database | PostgreSQL | 16-alpine |
| AI | Internal AI Gateway → Qwen3.5-122B | OpenAI-compatible |
| Frontend | React + TypeScript + Vite | 18 / 5+ |
| Styling | Tailwind CSS | 3+ |
| Export | python-docx + Jinja2 + mistune | — |
| Auth | python-jose (JWT) + PBKDF2-HMAC-SHA256 | — |
| Retry | tenacity (×3, exponential backoff) | 8.2+ |
| Deploy | Docker Compose + Dokploy + Traefik | — |

**Docker сервисы:** `db` (PostgreSQL) + `backend` (FastAPI) + `frontend` (React/nginx)

---

## 8. Нормативная база

| Документ | Применение |
|---|---|
| ICH E6(R2) | Международный стандарт GCP |
| GCP ЕАЭС (Решение ЕЭК №79, ред. №63 от 01.08.2025) | Основной с 01.09.2024, замена Приказа №200н |
| 61-ФЗ (гл. 7, ст. 38–44) | Правовая основа КИ в РФ |
| Приказ Минздрава №353н от 26.05.2021 | Информированное согласие |
| Приказ Минздрава №75н от 17.02.2025 | Изменения в протокол |
| Приказ Минздрава №708н от 23.12.2024 | Реестр разрешений на КИ |
| Решение Совета ЕЭК №77 | GMP ЕАЭС (исследуемые препараты) |
| ГОСТ Р 52379-2005 | Национальный стандарт GCP |
| 152-ФЗ | Защита персональных данных |

---

## 9. Документация

| Артефакт | Файл | Версия |
|---|---|---|
| README | `README.md` | 2.0.0 |
| Architecture (C4) | `ARCHITECTURE.md` | 1.2.0 |
| Checkpoint | `CHECKPOINT.md` | 7.0.0 |
| Deploy Guide | `DEPLOY.md` | 1.0.0 |
| Prompts | `PROMPTS.md` | 1.0.0 |
| Release Notes | `RELEASE-NOTES.md` | 2.0.0 |
| API Spec | `docs/api-spec.md` | 1.5.0 |
| Test Plan | `docs/test-plan.md` | 3.2.0 |
| Manual Test Guide | `docs/manual-test-guide.md` | 1.0.0 |
| Debug Guide | `docs/debug-guide.md` | 1.0.0 |
| Functional Requirements | `docs/functional-requirements.md` | 1.2.0 |
| Artifacts Catalog | `docs/artifacts-catalog.md` | 1.2.0 |
| Versions Registry | `docs/VERSIONS.md` | 1.3.0 |
| Metrics (этот файл) | `docs/METRICS.md` | 1.0.0 |
| 3× ADRs | `docs/adr/` | v1-2 |

**Всего артефактов:** 14 основных (A-001..014) + 15 вспомогательных (S-001..015)

---

## 10. Безопасность и соответствие требованиям

| Требование | Статус |
|---|---|
| NFR-08: только внутренний AI Gateway, внешние LLM запрещены | ✅ |
| NFR-05: audit_log с duration_ms для AI-вызовов | ✅ |
| Non-root user в Docker контейнерах | ✅ |
| Пароли через PBKDF2-HMAC-SHA256 (не bcrypt — нет зависимостей) | ✅ |
| JWT токены с configurable SECRET_KEY | ✅ |
| CORS только для разрешённых origins | ✅ |
| Secrets только через env vars (не хардкод) | ✅ |
| .env в .gitignore | ✅ |
| Watermark "FOR REVIEW ONLY" на AI-контенте | ✅ |

---

## 11. Оценка системы (peer review)

| Критерий | Оценка | Комментарий |
|---|---|---|
| Total Value | 7.0/10 | Реальный GCP compliance, RBAC, audit — но AI Gateway offline локально |
| Style | 7.0/10 | Synthia брендинг, SynthiaOrb, role-based UI — нет mobile layout |
| Innovation | 7.5/10 | Internal-only LLM, dual compliance scoring, pgvector RAG запланирован |
| Quality | 7.5/10 | 136 тестов, полная документация, clean async arch |
| **Итого** | **7.3/10** | **Вердикт: Continue** |

---

## 12. Статус фаз на момент сохранения контекста

| Фаза | Название | Готовность |
|---|---|---|
| Фаза 0 | Документация | ✅ 100% |
| Фаза 1 | Backend | ✅ 100% |
| Фаза 1.5 | Swagger Verification | ✅ 100% |
| Фаза 2 | Frontend | ✅ 100% |
| Фаза 2.5 | QA Testing | ✅ 100% |
| **Фаза 3** | **Deploy (Dokploy)** | **🔄 In Progress** |
| Фаза 4 | P1 Features | ✅ 100% |
| Фаза 5 | P2 Features | 📋 Backlog |
| Фаза 6 | P3 (RAG + Integrations) | 📋 Post-MVP |

---

## 13. Что нужно для завершения (до дедлайна 17:30)

| Задача | Приоритет | Оценка |
|---|---|---|
| Открыть Dokploy UI | P0 | 5 мин |
| Создать проект, подключить GitLab repo | P0 | 10 мин |
| Ввести env vars в Dokploy | P0 | 10 мин |
| Добавить домен (Dokploy генерирует) | P0 | 5 мин |
| Запустить Deploy | P0 | 20-40 мин (сборка образов) |
| Финальный smoke test на prod URL | P0 | 15 мин |
| Зафиксировать публичный URL | P0 | 2 мин |

**Итого remaining: ~1-1.5 часа при наличии Dokploy URL**

---

*Сохранено: 2026-04-24 | Сессия 7 | Подготовлено для презентации заказчику*
