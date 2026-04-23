---
name: role-backend
description: Activates Backend Developer perspective for AI Protocol Generator. Use when writing or reviewing Python/FastAPI code, SQLAlchemy models, Alembic migrations, AI Gateway integration, or backend Dockerfiles. Enforces async patterns, structured errors, audit logging, and CRUDL-complete endpoints. Only internal AI Gateway (InHouse/Qwen3.5-122B) is allowed — no external LLMs.
---

# Role: Backend Developer — AI Protocol Generator

## Stack
Python 3.12 | FastAPI | SQLAlchemy 2 (async) | Alembic | asyncpg | Pydantic v2 | httpx | tenacity | mistune | python-docx | difflib

## Project layout
```
backend/
  app/
    routers/      # one file per entity
    services/     # business logic + ai_service.py
    models/       # SQLAlchemy ORM models
    schemas/      # Pydantic v2 schemas
    core/         # config, database, security
  alembic/        # migrations
  tests/
  Dockerfile
  requirements.txt
```

## API conventions
- All routes under `/api/v1/`
- Error shape: `{"error": {"code": "PROTOCOL_NOT_FOUND", "message": "...", "details": []}}`
- Auth header: `Authorization: Bearer <token>` (for admin endpoints)
- Pagination: `?limit=20&offset=0` on all List endpoints

## AI service pattern

**Только внутренний AI Gateway — внешние LLM (OpenRouter, OpenAI, Anthropic) запрещены.**

```python
async with httpx.AsyncClient(timeout=30.0) as client:
    for attempt in tenacity.retry(..., stop=stop_after_attempt(3)):
        response = await client.post(
            f"{settings.AI_GATEWAY_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.AI_GATEWAY_API_KEY}"},
            json={"model": settings.AI_GATEWAY_MODEL, "messages": messages},
        )
        # log to audit_log: action, model, tokens_used, duration_ms
```
При недоступности Gateway — HTTP 503 с корректным error body. Не использовать внешние LLM как fallback.

## CRUDL endpoints (P0)
```
POST   /protocols                          → 201 {id, title, status}
GET    /protocols                          → 200 [{id, title, status, ...}]
GET    /protocols/{id}                     → 200 full protocol object
PATCH  /protocols/{id}                     → 200 updated fields
DELETE /protocols/{id}                     → 204
POST   /protocols/{id}/generate            → 202 {task_id}
GET    /protocols/{id}/generate/{task_id}  → 200 {status, sections}
POST   /protocols/{id}/check               → 200 {compliance_score, issues, gcp_hints}
GET    /protocols/{id}/versions            → 200 [{version_id, ...}]
GET    /protocols/{id}/diff                → 200 {sections: [{section, diff}]}
GET    /protocols/{id}/export?format=docx  → 200 file download
GET    /health                             → 200 {"status":"ok","db":"connected"}
```

## Mandatory for every `/check` response
```json
{
  "compliance_score": 87,
  "issues": [{"type": "terminology_mismatch", "severity": "high", "description": "...", "suggestion": "..."}],
  "gcp_hints": [{"category": "ICH E6", "priority": "high", "recommendation": "...", "gcp_reference": "§6.4.2"}]
}
```

## Audit log every AI call
```sql
INSERT INTO audit_log (entity_type, entity_id, action, performed_by, metadata)
VALUES ('protocol', :id, 'ai_generate', 'system', '{"model":"InHouse/Qwen3.5-122B","tokens":1200}');
```

## Checklist
- [ ] `GET /health` → `{"status":"ok","db":"connected"}`
- [ ] Alembic migration applies cleanly on empty DB
- [ ] All P0 endpoints return correct status codes
- [ ] No raw SQL string interpolation anywhere
