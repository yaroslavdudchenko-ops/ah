# ADR-003: FastAPI + React SPA как основной стек

**Status:** Accepted | **Date:** 2026-04-23 | **Version:** 1.0.0 | **Author:** System Architect

---

## Контекст

Нужно выбрать фреймворки для backend и frontend с учётом: дедлайн ~27 часов, требование деплоя на Dokploy, AI-интеграция, экспорт DOCX, версионирование документов.

## Backend

### Рассмотренные варианты

| Вариант | За | Против |
|---|---|---|
| **Python + FastAPI** | Async из коробки; python-docx для DOCX; difflib в stdlib; AI-интеграции нативны; быстро пишется | — |
| **Node.js + Express** | Единый язык с фронтом | DOCX библиотеки хуже; async AI менее удобен |
| **Django** | ORM мощный | Избыточен; sync по умолчанию; медленнее для MVP |

### Решение

**Python 3.12 + FastAPI + SQLAlchemy 2 (async) + Alembic**

### Обоснование (Rationale)

- FastAPI генерирует Swagger UI из коробки (`/docs`) — документация API без дополнительных усилий
- `python-docx` — нет аналогов в Node.js для DOCX генерации
- `difflib` из stdlib — diff секций без зависимостей
- Alembic — управление миграциями БД

## Frontend

### Рассмотренные варианты

| Вариант | За | Против |
|---|---|---|
| **React 18 + Vite + TypeScript** | Быстрый старт; SPA без SSR; собирается в статику; nginx раздаёт | — |
| **Next.js** | SSR; fullstack в одном репо | SSR избыточен; сложнее Docker setup; дольше настраивать |
| **Vue 3** | Легче React | Меньше экосистема UI компонентов |

### Решение

**React 18 + Vite + TypeScript + Tailwind CSS**

- Vite собирает статику за секунды
- Tailwind — быстрый UI без написания CSS с нуля
- Статика раздаётся nginx в том же контейнере, который проксирует `/api/*` → backend

## Деплой

Три сервиса в `docker-compose.yml`: `frontend` (nginx), `backend` (python), `db` (postgres).  
Dokploy настраивает домен на `frontend:80`. Traefik → nginx → React SPA + proxy /api → FastAPI.

## Последствия

- Монорепо: `backend/` и `frontend/` в одном репозитории
- Два `Dockerfile` (multi-stage): один для Python, один для React → nginx
- `nginx.conf` содержит правила proxy_pass для API
- Swagger UI доступен на `/docs` (только в development/staging окружении)
