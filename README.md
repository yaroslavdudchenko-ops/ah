# AI-генератор протоколов клинических исследований

**Version:** 1.0.0 | **Date:** 2026-04-23 | **Status:** Draft

---

## Описание

Веб-сервис для автоматизированной генерации черновиков протоколов клинических исследований (КИ) в соответствии со стандартами GCP/ICH. Сервис принимает структурированные входные параметры (фаза, индикация, популяция, конечные точки, дозирование), генерирует полноструктурированный документ с помощью внутреннего AI Gateway (InHouse/Qwen3.5-122B), контролирует консистентность терминологии и поддерживает версионирование документов.

Разработан в контексте фармацевтической компании полного цикла для снижения времени подготовки первичного черновика протокола и устранения «хвостов» от старых дизайнов при адаптации протоколов.

---

## Возможности

- **Библиотека шаблонов** — фаза I / II / III, рандомизированное, открытое, плацебо-контролируемое
- **AI-генерация разделов** — введение, цели, дизайн, эффективность, безопасность, статистика, этика
- **Контроль консистентности** — единый МНН/название препарата по всему документу, выявление логических противоречий
- **Версионирование** — v0.1, v0.2, ...; комментарии к версиям; diff на уровне секций
- **Артефакты** — заготовки SAP (Statistical Analysis Plan) и ICF (Informed Consent Form)
- **Экспорт** — Markdown, HTML, DOCX; список открытых вопросов для медицинского ревьюера

---

## Архитектура

```
Frontend (React 18 + Vite + TypeScript + Tailwind)
    ↕ REST API (/api/*)
Backend (Python 3.12 + FastAPI)
    ↕ asyncpg          ↕ httpx async
PostgreSQL 16      AI Gateway (InHouse/Qwen3.5-122B)
```

Подробная архитектура (C4 L1–L3, ER-диаграмма, deploy-граф): [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Стек

| Слой | Технология |
|---|---|
| Frontend | React 18, Vite, TypeScript, Tailwind CSS |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Alembic |
| База данных | PostgreSQL 16 (JSONB для секций протокола) |
| AI | AI Gateway — InHouse/Qwen3.5-122B (только локальные модели) |
| Экспорт | python-docx, Jinja2, markdown |
| Контейнеризация | Docker, Docker Compose |
| Деплой | Dokploy (Docker Compose mode) |

---

## Требования

- Docker Engine 24+
- Docker Compose v2.20+
- Доступ к внутреннему AI Gateway (`AI_GATEWAY_URL` + `AI_GATEWAY_API_KEY`)

---

## Быстрый старт

```bash
git clone https://github.com/<username>/research-protocol-generator.git
cd research-protocol-generator
cp .env.example .env
# Заполни .env: AI_GATEWAY_URL, AI_GATEWAY_API_KEY, POSTGRES_PASSWORD
docker compose up --build
```

Приложение доступно на `http://localhost:80`.

---

## Документация

| Документ | Описание |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | C4-диаграммы, ER-схема, deploy-граф |
| [DEPLOY.md](DEPLOY.md) | Инструкция деплоя на Dokploy |
| [PROMPTS.md](PROMPTS.md) | История промптов к AI-агенту |
| [docs/functional-requirements.md](docs/functional-requirements.md) | Функциональные требования |
| [docs/api-spec.md](docs/api-spec.md) | Спецификация REST API |
| [docs/adr/](docs/adr/) | Architecture Decision Records |
| [docs/VERSIONS.md](docs/VERSIONS.md) | Реестр версий документации |

---

## Принятые решения

Краткий обзор ключевых архитектурных решений:

- **PostgreSQL + JSONB** вместо SQLite — версионирование требует diff на уровне секций; JSONB даёт гибкость структуры без миграций при добавлении новых разделов. [ADR-001](docs/adr/ADR-001-postgresql.md)
- **AI Gateway (InHouse/Qwen3.5-122B)** — единственный LLM-провайдер; данные КИ не покидают внутренний контур (политика ИБ, NFR-08). [ADR-002](docs/adr/ADR-002-openrouter.md)
- **FastAPI + React SPA** вместо Next.js fullstack — разделение ответственности, независимые контейнеры, нет избыточного SSR для этого типа приложения. [ADR-003](docs/adr/ADR-003-stack.md)

---

## Демо-данные

Два синтетических протокола для демонстрации всех функций:

**Протокол 1 — Фаза II, онкология (открытое исследование)**
- Препарат: BCD-100 (Пролголимаб, PD-1 ингибитор)
- Индикация: Метастатическая меланома, прогрессия на 1 линии
- Primary endpoint: ORR по RECIST 1.1

**Протокол 2 — Фаза III, дерматология (рандомизированное двойное слепое)**
- Препарат: BCD-089 (IL-17A ингибитор)
- Индикация: Псориаз среднетяжёлый и тяжёлый (PASI ≥ 12)
- Primary endpoint: PASI 75 на 12 неделе

---

## Разработка

```bash
# Backend (локально без Docker)
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (локально без Docker)
cd frontend
npm install
npm run dev
```

## Тестирование

```bash
# Backend unit tests
cd backend && pytest

# Полный стек (Docker)
docker compose up --build
# API docs: http://localhost:8000/docs
# App: http://localhost:80
```

## Лицензия

MIT
