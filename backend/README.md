# Backend — AI Protocol Generator

**Version:** 1.0.0 | **Date:** 2026-04-23

Python 3.12 + FastAPI + SQLAlchemy 2 (async) + Alembic + PostgreSQL 16

---

## Структура

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, lifespan, middleware
│   ├── config.py                # Settings (pydantic-settings)
│   ├── database.py              # AsyncEngine, SessionLocal
│   ├── api/
│   │   ├── __init__.py
│   │   ├── protocols.py         # /api/v1/protocols
│   │   ├── templates.py         # /api/v1/templates
│   │   ├── generate.py          # /api/v1/protocols/{id}/generate
│   │   ├── export.py            # /api/v1/protocols/{id}/export
│   │   └── health.py            # /health
│   ├── models/
│   │   ├── __init__.py
│   │   ├── protocol.py          # Protocol, ProtocolVersion SQLAlchemy models
│   │   ├── template.py          # Template model
│   │   ├── terminology.py       # Terminology model
│   │   ├── open_issue.py        # OpenIssue model
│   │   └── audit_log.py         # AuditLog model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── protocol.py          # Pydantic request/response schemas
│   │   ├── template.py
│   │   └── common.py            # Pagination, Error schemas
│   └── services/
│       ├── __init__.py
│       ├── ai.py                # AIGatewayClient (httpx async, tenacity retry, InHouse/Qwen3.5-122B)
│       ├── generator.py         # GeneratorService — формирует промпты, вызывает AI
│       ├── consistency.py       # ConsistencyService — проверка терминологии и противоречий
│       ├── export.py            # ExportService — MD / HTML / DOCX
│       └── diff.py              # DiffService — difflib секций между версиями
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py
├── tests/
│   ├── conftest.py
│   ├── test_protocols.py
│   └── test_ai_service.py
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
└── alembic.ini
```

## Зависимости (requirements.txt)

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
httpx>=0.27.0
python-docx>=1.1.0
jinja2>=3.1.0
tenacity>=8.2.0
```

## Запуск

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Swagger UI: http://localhost:8000/docs
