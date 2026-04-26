# Debug Guide — Synthia AI Protocol Generator

**Version:** 1.0.0 | **Date:** 2026-04-23 | **Status:** Active  
**Artifact ID:** A-015

> Живой отчёт дебаг-сессии + инструкции по диагностике и устранению неисправностей.

---

## Результаты живой дебаг-сессии (2026-04-23)

### Состояние системы

| Компонент | Статус | Детали |
|---|---|---|
| `GET /health` | ✅ OK | `{"status":"ok","db":"connected"}` |
| Backend (FastAPI) | ✅ healthy | port 52019 |
| Frontend (nginx) | ✅ healthy | port 52020 |
| PostgreSQL 16 | ✅ healthy | port 52003 |
| AI Gateway (Ollama) | ⚠️ OFFLINE | `host.docker.internal:11434` — не запущен |

### Статистика БД

| Таблица | Записей |
|---|---|
| `protocols` | 4 |
| `protocol_versions` | 22 |
| `audit_log` | 47 |
| `templates` | 3 |
| `open_issues` | 5 |

### Состояние протоколов

| Препарат | Фаза | Статус | Область | Теги |
|---|---|---|---|---|
| BCD-100 | II | generated | oncology | [] ⚠️ |
| BCD-089 | III | generated | dermatology | [] ⚠️ |
| BCD-021 | III | approved | hematology | [] ⚠️ |
| BCD-132 | I | draft | oncology | [] ⚠️ |

### Пройденные проверки безопасности (RBAC)

| Проверка | Результат |
|---|---|
| `POST /protocols` без токена | ✅ 401 |
| `POST /protocols` как auditor | ✅ 403 |
| `DELETE /protocols/{id}` как employee | ✅ 403 |
| `POST /protocols` `phase="II"` | ✅ 201 |
| `POST /protocols` `phase="phase_2"` | ✅ 422 |
| Export MD для generated протокола | ✅ 200 OK (backend) |

---

## Найденные проблемы

### ⚠️ ISSUE-1: Теги пустые во всех протоколах в БД

**Серьёзность:** Medium  
**Описание:** Все 4 демо-протокола имеют `tags: []`. Функция тегов реализована, но seed-скрипт не заполнил теги.  
**Влияние:** Фильтр по тегам в UI возвращает пустой список, `/tags` endpoint возвращает `[]`.

**Быстрое исправление:**
```bash
docker compose exec backend python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.protocol import Protocol
from sqlalchemy import select

async def fix():
    engine = create_async_engine(settings.DATABASE_URL)
    Session = async_sessionmaker(engine)
    async with Session() as db:
        tags_map = {
            'BCD-100': ['онкология','pd-1','фаза-2','меланома'],
            'BCD-089': ['дерматология','il-17','биоаналог','псориаз'],
            'BCD-021': ['онкология','cd20','биоаналог','лимфома'],
            'BCD-132': ['ревматология','биоаналог','фаза-1'],
        }
        for drug, tags in tags_map.items():
            r = await db.execute(select(Protocol).where(Protocol.drug_name==drug))
            p = r.scalar_one_or_none()
            if p:
                p.tags = tags
                db.add(p)
        await db.commit()
        print('Tags fixed!')

asyncio.run(fix())
"
```

**Постоянное исправление:** Обновить `seed_demo.py` чтобы заполнял `tags` при создании протоколов.

---

### ⚠️ ISSUE-2: AI Gateway OFFLINE

**Серьёзность:** High (блокирует генерацию новых протоколов)  
**Описание:** `AI_GATEWAY_URL=http://host.docker.internal:11434` — Ollama не запущен на хосте.  
**Влияние:** `POST /{id}/generate` возвращает 202 (принято), но фоновая задача падает со статусом `failed`.

**Диагностика:**
```bash
# Проверить что gateway недоступен
curl http://localhost:11434/api/tags

# Проверить config в контейнере
docker compose exec backend env | grep AI_GATEWAY
```

**Варианты исправления:**

| Вариант | Команда |
|---|---|
| Запустить Ollama локально | `ollama serve` (после `ollama pull qwen2.5:72b`) |
| Указать реальный AI Gateway | В `.env`: `AI_GATEWAY_URL=https://your-gateway.domain` |
| Mock для тестирования | Используй тесты с `mock_ai_gateway_ok` фикстурой |

**Настройка `.env.local`:**
```bash
AI_GATEWAY_URL=http://host.docker.internal:11434
AI_GATEWAY_API_KEY=dev-key
AI_GATEWAY_MODEL=InHouse/Qwen3.5-122B
```

---

### ℹ️ ISSUE-3: `Invoke-WebRequest` зависает на больших ответах (только PowerShell)

**Серьёзность:** Low (не влияет на работу системы)  
**Описание:** PowerShell `Invoke-WebRequest` зависает при загрузке больших MD/DOCX файлов.  
**Бэкенд возвращает 200 OK** — видно в логах. Проблема в клиенте, не в сервере.

**Обходной путь:**
```powershell
# Использовать -OutFile вместо чтения в переменную
Invoke-WebRequest "$BASE/protocols/{id}/export?format=md" -Headers $h -OutFile "export.md"
```

---

## Диагностические команды

### Быстрый health-check

```bash
# Все контейнеры
docker compose ps

# Health endpoint
curl http://localhost:52019/health

# Логи в реальном времени
docker compose logs -f backend
```

### Получить токен

```bash
curl -X POST http://localhost:52019/api/v1/auth/token \
  -d "username=admin&password=admin123" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

### Тестовые запросы (curl)

```bash
BASE=http://localhost:52019/api/v1
TOKEN=<token_from_above>

# Список протоколов
curl -H "Authorization: Bearer $TOKEN" $BASE/protocols | jq '.[].drug_name'

# Теги
curl -H "Authorization: Bearer $TOKEN" $BASE/tags

# Создать протокол (валидная фаза: I, II, III, IV)
curl -X POST $BASE/protocols \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Protocol BCD-100",
    "drug_name": "BCD-100",
    "inn": "Пролголимаб",
    "phase": "II",
    "therapeutic_area": "Онкология",
    "indication": "Метастатическая меланома прогрессия",
    "population": "Взрослые пациенты 18 лет и старше",
    "primary_endpoint": "ORR по RECIST 1.1",
    "secondary_endpoints": ["PFS", "OS"],
    "duration_weeks": 96,
    "dosing": "1 мг/кг каждые 2 недели"
  }'

# Запустить генерацию (заменить {id} на реальный id)
curl -X POST $BASE/protocols/{id}/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sections": null}'

# Проверить статус задачи
curl -H "Authorization: Bearer $TOKEN" $BASE/protocols/{id}/generate/{task_id}

# GCP-проверка
curl -X POST $BASE/protocols/{id}/check \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"version_id": null}'

# Экспорт MD
curl -H "Authorization: Bearer $TOKEN" $BASE/protocols/{id}/export?format=md -o out.md

# Экспорт DOCX
curl -H "Authorization: Bearer $TOKEN" $BASE/protocols/{id}/export?format=docx -o out.docx
```

### Диагностика БД

```bash
# Подключиться к PostgreSQL
docker compose exec db psql -U app -d protocols

# Состояние таблиц
SELECT table_name, (SELECT count(*) FROM information_schema.columns WHERE table_name=t.table_name) AS cols
FROM information_schema.tables t WHERE table_schema='public';

# Протоколы
SELECT drug_name, phase, status, tags FROM protocols;

# Последние audit события
SELECT action, performed_by, created_at FROM audit_log ORDER BY created_at DESC LIMIT 10;

# Проблемные issues
SELECT protocol_id, section, severity, issue_type FROM open_issues WHERE resolved=false;

# Миграции
SELECT version_num, description FROM alembic_version;
```

### Диагностика контейнеров

```bash
# Логи по уровню
docker compose logs backend 2>&1 | grep -E "ERROR|CRITICAL"

# Переменные окружения backend
docker compose exec backend env | sort

# Использование ресурсов
docker stats --no-stream

# Перезапуск только одного сервиса
docker compose restart backend

# Полная пересборка без кэша
docker compose build --no-cache backend
docker compose up -d --force-recreate backend
```

---

## Распространённые ошибки и решения

### `Connection refused` или `ERR_CONNECTION_REFUSED`

```
Причина: Docker порты изменились после перезапуска
Решение: docker compose ps  →  найти актуальный порт
```

### `HTTP 503 – AI Gateway недоступен`

```
Причина: AI_GATEWAY_URL недоступен внутри контейнера
Диагностика:
  docker compose exec backend curl $AI_GATEWAY_URL/health
Решение: Проверить host.docker.internal vs localhost
  В .env: AI_GATEWAY_URL=http://host.docker.internal:11434
```

### `HTTP 422 – Unprocessable Entity` при создании протокола

```
Частые причины:
  - phase не в формате I/II/III/IV (не phase_1!)
  - duration_weeks = 0 или > 520
  - indication < 10 символов
  - title < 5 символов
  - primary_endpoint < 3 символов

Проверка: смотри детали ошибки в response body:
  {"detail": [{"type": "...", "loc": [...], "msg": "..."}]}
```

### `HTTP 422 – NO_CONTENT` при экспорте или GCP-check

```
Причина: Протокол создан, но генерация не запускалась
Решение: POST /protocols/{id}/generate  →  подождать task_id=completed
```

### Frontend не обновляется после rebuild

```bash
# Принудительная пересборка + рестарт
docker compose build --no-cache frontend
docker compose up -d --force-recreate frontend

# Очистить кэш браузера (Ctrl+Shift+Delete)
```

### Тесты падают с `asyncpg.connect timeout`

```bash
# Убедиться что protocols_test БД существует
docker compose exec db psql -U app -c "\l" | grep protocols_test

# Если нет — создать
docker compose exec db psql -U app -c "CREATE DATABASE protocols_test;"
```

---

## Чеклист дебага перед деплоем

```
[ ] docker compose ps — все 3 контейнера Healthy
[ ] GET /health → {"status":"ok","db":"connected"}
[ ] Все 3 роли (admin/employee/auditor) авторизуются
[ ] POST /protocols с phase="II" → 201
[ ] POST /protocols с phase="phase_2" → 422
[ ] GET /protocols → массив протоколов
[ ] GET /tags → массив тегов (если теги добавлены)
[ ] GET /templates → 3 шаблона
[ ] GET /audit-log → не пустой
[ ] Нет ERROR в docker compose logs backend --tail=50
[ ] 136 automated tests pass: docker compose exec backend pytest tests/ -q
```

---

## Архитектура потоков для дебага

```
UI (браузер :52020)
    ↓ HTTP
nginx (frontend)
    ↓ /api/v1/* proxy_pass
FastAPI (backend :8000/:52019)
    ├── auth → JWT verify
    ├── protocols → PostgreSQL (db:5432/:52003)
    ├── generate → BackgroundTask → AI Gateway (host.docker.internal:11434)
    ├── check → consistency.py → AI Gateway
    └── export → mistune/python-docx → FileResponse
```

### Типичный флоу генерации (для дебага):

```
POST /generate          →  202 + task_id
                           background task запущен
GET /generate/{task_id} →  {status: "pending"}  (задача в очереди)
GET /generate/{task_id} →  {status: "running"}   (AI генерирует)
GET /generate/{task_id} →  {status: "completed"} (готово, sections_done: [...])
                        →  {status: "failed"}     (AI Gateway недоступен)
```

**Если `status: "failed"` — смотреть поле `error` в ответе и логи:**
```bash
docker compose logs backend 2>&1 | grep -A5 "generation_failed"
```

---

## Мониторинг в реальном времени

```bash
# Логи всех сервисов
docker compose logs -f

# Только ошибки backend
docker compose logs -f backend 2>&1 | grep -E "ERROR|WARN|Critical"

# Статистика запросов (из uvicorn access log)
docker compose logs backend 2>&1 | grep "HTTP/1.1" | awk '{print $8, $9}' | sort | uniq -c | sort -rn
```
