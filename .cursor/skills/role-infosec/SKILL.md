---
name: role-infosec
description: Activates Information Security Specialist perspective for AI Protocol Generator. Use when reviewing security, secrets management, Docker hardening, API authentication, input validation, prompt injection prevention, audit logging, or OWASP compliance. Triggers: security review, infosec, secrets, vulnerability, CORS, SQL injection, audit trail, pen test, dependency scan.
---

# Role: Information Security Specialist — AI Protocol Generator

## Security domains
1. Secrets & credentials management
2. API input validation & sanitization
3. AI prompt injection prevention
4. Container hardening (Docker)
5. Audit trail completeness
6. Dependency vulnerability scanning
7. Export & data protection

---

## 1. Secrets management

**Never commit:**
```bash
git grep -rn "sk-or-\|password=\|secret=" --include="*.py" --include="*.ts"
# Must return empty
```

**Required `.gitignore` entries:**
```
.env
.env.local
*.pem
*.key
```

**`.env.example` template** (no real values):
```
OPENROUTER_API_KEY=sk-or-<REPLACE_WITH_REAL>
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/protocols
SECRET_KEY=<openssl rand -hex 32>
CORS_ORIGINS=http://localhost:80
LOG_LEVEL=INFO
APP_ENV=production
```

---

## 2. API input validation

Every FastAPI endpoint must use a Pydantic model — no raw body access:

```python
# ✅ CORRECT
class ProtocolCreate(BaseModel):
    title: str = Field(min_length=5, max_length=200)
    phase: Literal["I", "II", "III"]
    duration_weeks: int = Field(gt=0, le=520)
    primary_endpoint: str = Field(min_length=3, max_length=500)
    drug_name: str = Field(min_length=1, max_length=200)

# ❌ WRONG
@app.post("/protocols")
async def create(request: Request):
    body = await request.json()  # no validation
```

---

## 3. AI prompt injection prevention

All user text going into prompts must be sanitized:

```python
BLOCKED_PATTERNS = [
    "ignore previous instructions",
    "system:", "[INST]", "<<SYS>>",
    "forget everything", "new instructions:"
]

def sanitize_for_prompt(text: str, max_length: int = 500) -> str:
    for pattern in BLOCKED_PATTERNS:
        if pattern.lower() in text.lower():
            raise HTTPException(400, "Invalid input content")
    return text.strip()[:max_length]
```

Apply to: `indication`, `population`, `primary_endpoint`, `dosing`, all free-text fields.

---

## 4. Container hardening

```dockerfile
# ✅ CORRECT backend Dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
RUN useradd -r -u 1001 -g root appuser
WORKDIR /app
COPY --from=builder --chown=appuser /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --chown=appuser . .
USER appuser
EXPOSE 8000
HEALTHCHECK CMD curl -f http://localhost:8000/health
```

---

## 5. Audit trail

Every state-changing operation must write to `audit_log`:

| Action | When |
|--------|------|
| `protocol_create` | POST /protocols |
| `protocol_update` | PATCH /protocols/{id} |
| `protocol_delete` | DELETE /protocols/{id} |
| `ai_generate` | POST /protocols/{id}/generate |
| `consistency_check` | POST /protocols/{id}/check |
| `export` | GET /protocols/{id}/export |

```python
await db.execute(
    insert(AuditLog).values(
        entity_type="protocol",
        entity_id=protocol_id,
        action=action,
        performed_by="system",
        request_id=request.headers.get("X-Request-ID"),
        metadata={"model": model, "tokens": tokens_used}
    )
)
```

---

## 6. Dependency scanning

```bash
# Before deploy:
pip-audit                    # Python CVEs
safety check -r requirements.txt

# Docker image scan (if trivy available):
trivy image protocol-backend:latest
```

---

## 7. Export data protection

```python
ALLOWED_EXPORT_FORMATS = {"md", "html", "docx"}
MAX_EXPORT_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

WATERMARK = "FOR DEMONSTRATION PURPOSES ONLY — SYNTHETIC DATA"
AI_DISCLAIMER = "AI-Assisted. Requires qualified person review."

def safe_export_filename(protocol_id: str, version: str, fmt: str) -> str:
    # No user-controlled data in filename
    return f"protocol_{protocol_id}_v{version}.{fmt}"
```

---

## Pre-deploy security checklist

```
[ ] git grep secrets → empty result
[ ] .env not committed
[ ] All endpoints have Pydantic models
[ ] Prompt sanitization applied to all text inputs
[ ] Non-root USER in all Dockerfiles
[ ] audit_log writes on all state changes
[ ] CORS_ORIGINS set to specific domain
[ ] pip-audit passes with 0 vulnerabilities
[ ] Export filenames use only safe identifiers
[ ] X-Request-ID header on all responses
```
