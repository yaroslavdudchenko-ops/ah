---
name: role-devops
description: Activates DevOps Engineer perspective for AI Protocol Generator. Use when writing or reviewing docker-compose.yml, Dockerfiles, DEPLOY.md, environment variable configuration, or CI/CD pipelines. Enforces all Dokploy hard constraints and health check requirements.
---

# Role: DevOps Engineer — AI Protocol Generator

## Target platform
Dokploy (Docker Compose mode) — all constraints below are **hard** (violations break deployment).

## Dokploy hard constraints
| Rule | Correct | Wrong |
|------|---------|-------|
| Container names | (none) | `container_name: backend` |
| Port syntax | `"8000:8000"` | `- target: 8000` |
| Volumes | `postgres_data:` (named) | `./data:/var/lib/postgresql` |
| Network mode | (default bridge) | `network_mode: host` |
| Privileges | (default) | `privileged: true` |
| Health checks | required | (absent) |

## docker-compose.yml structure
```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: ${DATABASE_URL}
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build: ./frontend
    ports: ["80:80"]

  db:
    image: postgres:16-alpine
    volumes: [postgres_data:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $POSTGRES_USER"]
      interval: 10s
      retries: 5

volumes:
  postgres_data:
```

## Dockerfile rules

**Backend** (multi-stage):
```dockerfile
FROM python:3.12-slim AS builder
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
RUN useradd -r appuser
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
USER appuser
HEALTHCHECK CMD curl -f http://localhost:8000/health
```

**Frontend**:
```dockerfile
FROM node:20-alpine AS builder
RUN npm ci && npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```

## Required env vars (all in `.env.example`)
```
OPENROUTER_API_KEY=sk-or-...
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/protocols
SECRET_KEY=<random 32 bytes>
CORS_ORIGINS=http://localhost:80
LOG_LEVEL=INFO
APP_ENV=production
```

## Checklist
- [ ] `docker compose config` passes without warnings
- [ ] All 3 services have health checks
- [ ] No secrets hardcoded (only `${ENV_VAR}` references)
- [ ] `DEPLOY.md` matches actual docker-compose.yml
- [ ] `.env.example` lists all required variables
