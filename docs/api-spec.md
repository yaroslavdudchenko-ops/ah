# REST API Specification

**Version:** 1.6.0 | **Date:** 2026-04-24 | **Status:** Active  
**Author:** System Architect  
**Standards:** CRUDL (полное покрытие операций для каждой сущности), ALCOA++

Base URL: `/api/v1`  
Content-Type: `application/json`

### Аутентификация

Все эндпоинты (кроме `/health`, `/auth/token`) требуют JWT Bearer token:

```
Authorization: Bearer <access_token>
```

Токен получается через `POST /auth/token` (OAuth2 Password Flow).

### RBAC — Матрица ролей

| Операция | admin | employee | auditor |
|---|---|---|---|
| GET (любой) | ✅ | ✅ | ✅ |
| POST /protocols | ✅ | ✅ | ❌ 403 |
| PATCH /protocols/{id} | ✅ | ✅ | ❌ 403 |
| DELETE /protocols/{id} | ✅ | ❌ 403 | ❌ 403 |
| POST /generate (не approved) | ✅ | ✅ | ❌ 403 |
| POST /generate (approved) | ❌ 423 | ❌ 423 | ❌ 423 |
| POST /check | ✅ | ✅ | ❌ 403 |
| POST /protocols/{id}/copy | ✅ | ✅ | ❌ 403 |
| PATCH …approved (не creator) | ✅ | ✅ | ❌ 403 |
| PATCH …approved (creator) | ❌ 403 | ❌ 403 | ❌ 403 |
| GET /audit-log | ✅ | ✅ | ✅ |
| GET /biocad-trials | ✅ | ✅ | ✅ |

### AI Provider

Все генерирующие и валидационные эндпоинты (`/generate`, `/check`) используют **только внутренний AI Gateway**:

| Параметр | Значение |
|---|---|
| Провайдер | AI Gateway (`AI_GATEWAY_URL`) |
| Модель | `InHouse/Qwen3.5-122B` (только локальные модели) |
| Интерфейс | OpenAI-compatible `POST /v1/chat/completions` |
| Клиент | `httpx.AsyncClient` + `tenacity` retry (3 попытки, exponential backoff) |
| Внешние LLM | **Не используются** — политика безопасности запрещает передачу данных протоколов КИ внешним сервисам |

### CRUDL-матрица

| Сущность | C | R | U | D | L |
|---|---|---|---|---|---|
| Protocol | POST /protocols | GET /protocols/{id} | PATCH /protocols/{id} | DELETE /protocols/{id} | GET /protocols |
| Template | POST /templates *(P2)* | GET /templates/{id} *(P2)* | PUT /templates/{id} *(P2)* | DELETE /templates/{id} *(P2)* | GET /templates |
| ProtocolVersion | via /generate | GET /protocols/{id}/versions/{vid} | N/A (immutable) | N/A (cascade) | GET /protocols/{id}/versions |
| OpenIssue | via /check | GET /protocols/{id}/open-issues | PATCH /open-issues/{id} | N/A (cascade) | included in GET |

---

## Аутентификация

### POST /auth/token
OAuth2 Password Flow — получить JWT access token.

**Request** (`application/x-www-form-urlencoded`)
```
grant_type=password&username=admin&password=admin_password
```

**Response 200**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "admin",
  "username": "admin"
}
```

**Response 401** — неверный логин/пароль.

---

### GET /auth/me
Получить информацию о текущем пользователе.

**Response 200**
```json
{
  "username": "admin",
  "role": "admin"
}
```

---

## Аудиторский след

### GET /audit-log
Глобальный журнал всех действий пользователей. Доступен всем ролям (read-only).

**Query params:**
- `from_date` — фильтр дат от (YYYY-MM-DD, включительно)
- `to_date` — фильтр дат до (YYYY-MM-DD, включительно)
- `action` — фильтр по действию (`create`, `update`, `delete`, `ai_generate`, `consistency_check`, `export`, `section_regenerate`)
- `performed_by` — фильтр по имени пользователя
- `limit` — количество записей (default 100, max 500)
- `offset` — смещение

**Response 200**
```json
[
  {
    "id": "uuid",
    "entity_type": "protocol",
    "entity_id": "uuid",
    "action": "ai_generate",
    "performed_by": "employee",
    "metadata": {
      "role": "employee",
      "model": "InHouse/Qwen3.5-122B",
      "duration_ms": 12450,
      "title": "Протокол BCD-100 Фаза II",
      "version": 3
    },
    "created_at": "2026-04-23T18:00:00Z"
  }
]
```

---

### GET /protocols/{id}/audit
Аудиторский след конкретного протокола. Доступен всем ролям.

**Query params:** `from_date`, `to_date`, `limit`, `offset`

**Response 200** — аналогично `GET /audit-log`, но только события этого протокола.

---

## Шаблоны

### GET /templates
Список всех шаблонов протоколов.

**Response 200**
```json
[
  {
    "id": "uuid",
    "name": "Phase II Oncology Open-Label",
    "phase": "II",
    "design_type": "open_label"
  }
]
```

---

### GET /templates/{id}
Получить шаблон по ID.

**Response 200**
```json
{
  "id": "uuid",
  "name": "Phase II Oncology Open-Label",
  "phase": "II",
  "design_type": "open_label",
  "section_prompts": {
    "introduction": "...",
    "objectives": "..."
  },
  "created_at": "2026-04-23T00:00:00Z"
}
```

---

### POST /templates *(P2 — admin only)*
Создать новый шаблон.

**Headers:** `X-Admin-Key: <admin_key>`

**Request**
```json
{
  "name": "Phase I FIH Open-Label",
  "phase": "I",
  "design_type": "open_label",
  "section_prompts": {
    "introduction": "Prompt text...",
    "objectives": "Prompt text..."
  }
}
```

**Response 201**
```json
{ "id": "uuid", "name": "Phase I FIH Open-Label", "phase": "I", "design_type": "open_label" }
```

---

### PUT /templates/{id} *(P2 — admin only)*
Полная замена шаблона.

**Headers:** `X-Admin-Key: <admin_key>`

**Request** — полная структура шаблона (см. POST /templates).  
**Response 200** — обновлённый объект шаблона.

---

### DELETE /templates/{id} *(P2 — admin only)*
Удалить шаблон. Протоколы, использующие шаблон, сохраняются (`template_id` становится null).

**Headers:** `X-Admin-Key: <admin_key>`  
**Response 204** No Content.

---

## Протоколы

### POST /protocols
Создать новый протокол.

**Request**
```json
{
  "title": "Протокол BCD-100 Фаза II",
  "template_id": "uuid",
  "phase": "II",
  "indication": "Метастатическая меланома",
  "population": "Взрослые 18+, ECOG 0-1, прогрессия на 1 линии терапии",
  "inclusion_criteria": [
    "Возраст ≥ 18 лет",
    "ECOG Performance Status 0-1",
    "Гистологически верифицированная меланома"
  ],
  "primary_endpoint": "ORR по RECIST 1.1",
  "secondary_endpoints": ["PFS", "OS", "DOR"],
  "duration_weeks": 96,
  "drug_name": "BCD-100",
  "inn": "Пролголимаб",
  "dosing": "1 мг/кг в/в каждые 2 недели",
  "exclusion_criteria": [
    "Аутоиммунные заболевания в анамнезе",
    "Системная иммуносупрессивная терапия"
  ]
}
```

**Response 201**
```json
{
  "id": "uuid",
  "title": "Протокол BCD-100 Фаза II",
  "phase": "II",
  "status": "draft",
  "created_at": "2026-04-23T14:00:00Z",
  "latest_version": null
}
```

---

### GET /protocols
Список протоколов с поиском и фильтрацией.

**Query params:**

| Параметр | Тип | Описание |
|---|---|---|
| `limit` | int | Макс. количество записей (default: 50, max: 100) |
| `offset` | int | Смещение для пагинации |
| `search` | string | Поиск по title и drug_name (case-insensitive, contains) |
| `phase` | string | Фильтр по фазе: `phase_1` \| `phase_2` \| `phase_3` \| `phase_4` |
| `status` | string | Фильтр по статусу: `draft` \| `generated` \| `in_review` \| `approved` \| `archived` |
| `therapeutic_area` | string | Фильтр по терапевтической области (contains) |
| `tag` | string | Фильтр по тегу (точное вхождение в массив) |

**Response 200** — массив объектов `ProtocolListItem`:
```json
[
  {
    "id": "uuid",
    "title": "BCD-100 Phase II Study",
    "drug_name": "BCD-100",
    "inn": "Пролголимаб",
    "phase": "phase_2",
    "therapeutic_area": "Онкология",
    "status": "generated",
    "tags": ["онкология", "phase-2"],
    "updated_at": "2026-04-23T20:35:00Z",
    "created_at": "2026-04-23T20:00:00Z"
  }
]
```

---

### GET /protocols/{id}
Получить протокол с последней версией контента.

**Response 200**
```json
{
  "id": "uuid",
  "title": "Протокол BCD-100 Фаза II",
  "phase": "II",
  "indication": "Метастатическая меланома",
  "population": "Взрослые 18+, ECOG 0-1",
  "primary_endpoint": "ORR по RECIST 1.1",
  "secondary_endpoints": ["PFS", "OS", "DOR"],
  "duration_weeks": 96,
  "drug_name": "BCD-100",
  "inn": "Пролголимаб",
  "dosing": "1 мг/кг в/в каждые 2 недели",
  "exclusion_criteria": ["Аутоиммунные заболевания в анамнезе"],
  "template_id": "uuid",
  "status": "draft",
  "created_at": "2026-04-23T14:00:00Z",
  "updated_at": "2026-04-23T14:30:00Z",
  "latest_version": {
    "id": "uuid",
    "version": "v0.1",
    "content": {
      "introduction": "...",
      "objectives": "...",
      "design": "...",
      "population": "...",
      "dosing": "...",
      "efficacy": "...",
      "safety": "...",
      "statistics": "...",
      "ethics": "..."
    },
    "created_at": "2026-04-23T14:30:00Z"
  }
}
```

---

### PATCH /protocols/{id}
Частичное обновление метаданных протокола. Версия контента не изменяется.

**Request** — любое подмножество полей:
```json
{
  "title": "Протокол BCD-100 Фаза II (уточнённый)",
  "indication": "Метастатическая меланома, линия 2+",
  "status": "review"
}
```

Допустимые значения `status`: `draft` | `review` | `final`

**Response 200** — полный объект protocol (см. GET /protocols/{id}).

---

### DELETE /protocols/{id}
Удалить протокол и все связанные данные (CASCADE: versions, open_issues, terminology, audit_log).

**Response 204** No Content.

> Операция необратима. Записи в `audit_log` удаляются вместе с протоколом. Перед удалением рекомендуется экспортировать все версии.

---

### POST /protocols/{id}/copy
Создать копию протокола в статусе `draft`. Исходный протокол и его версии не изменяются.

**Auth:** admin, employee  
**Response 201** — новый `ProtocolResponse` с `status: "draft"`, теми же метаданными, но без версий контента.

**Ограничения:** `created_by` новой копии = текущий пользователь.

---

### POST /protocols/{id}/fork
Создать форк (ревизию) протокола. Текущий протокол помечается как `archived`.

**Auth:** admin, employee  
**Response 201** — новый `ProtocolResponse` в статусе `draft`.

---

### PATCH /protocols/{id} — approve (4-eyes)
Изменение статуса на `approved`. Недоступно для `created_by` протокола.

**HTTP 403** `SELF_APPROVAL_FORBIDDEN` — если текущий пользователь является создателем.

---

## Генерация

### POST /protocols/{id}/generate
Запустить AI-генерацию всех секций. Создаёт новую версию протокола.

**Request**
```json
{
  "comment": "Первичная генерация",
  "sections": ["introduction", "objectives", "design", "population",
               "dosing", "efficacy", "safety", "statistics", "ethics"]
}
```

> `sections` — опциональный список для частичной перегенерации. Если не указан — генерируются все секции.

**Response 202**
```json
{
  "task_id": "uuid",
  "status": "pending",
  "version": "v0.1"
}
```

### GET /protocols/{id}/generate/{task_id}
Статус задачи генерации (polling).

**Response 200**
```json
{
  "task_id": "uuid",
  "status": "completed",
  "version_id": "uuid",
  "version": "v0.2",
  "elapsed_seconds": 45
}
```

`status`: `pending` | `running` | `completed` | `failed`

---

### POST /protocols/{id}/sections/{section_key}/regenerate
Перегенерация отдельной секции протокола (FR-03.5). Требует роль `admin` или `employee`.

**Path params:** `section_key` — ключ секции (`introduction`, `objectives`, `design`, `population`, `dosing`, `efficacy`, `safety`, `statistics`, `ethics`)

**Response 202**
```json
{
  "task_id": "uuid",
  "section": "statistics",
  "status": "pending"
}
```

Статус отслеживается через `GET /protocols/{id}/generate/{task_id}`.

---

## Консистентность

### POST /protocols/{id}/check
Проверить консистентность терминологии и логическую согласованность секций.

**Request**
```json
{
  "version_id": "uuid"
}
```

**Response 200**
```json
{
  "compliance_score": 78,
  "issues": [
    {
      "type": "terminology_mismatch",
      "severity": "medium",
      "sections": ["introduction", "dosing"],
      "description": "Препарат назван 'BCD-100' в введении и 'пролголимаб' в дозировании — требуется единообразие",
      "suggestion": "Используйте единую форму: 'Пролголимаб (BCD-100)'"
    },
    {
      "type": "endpoint_mismatch",
      "severity": "high",
      "sections": ["efficacy", "statistics"],
      "description": "Первичная конечная точка ORR не упомянута в плане статистического анализа",
      "suggestion": "Добавьте метод анализа ORR в раздел статистики"
    },
    {
      "type": "population_inconsistency",
      "severity": "medium",
      "sections": ["population", "design"],
      "description": "Возрастные критерии включения/исключения конфликтуют",
      "suggestion": "Согласуйте возрастные ограничения в разделах 3 и 4"
    }
  ],
  "gcp_hints": [
    {
      "category": "ethics",
      "priority": "high",
      "recommendation": "Раздел 'Этика' не содержит ссылку на Хельсинкскую декларацию",
      "gcp_reference": "ICH E6 R2 §3.1"
    },
    {
      "category": "safety",
      "priority": "medium",
      "recommendation": "Отсутствует описание процедуры рандомизации",
      "gcp_reference": "ICH E6 R2 §5.7"
    }
  ],
  "summary": "Обнаружено 3 несоответствия, 2 GCP-подсказки. Требуется проверка специалистом."
}
```

**Возможные значения `type`:** `terminology_mismatch` | `endpoint_mismatch` | `population_inconsistency` | `duration_mismatch` | `dosing_inconsistency` | `sample_size_endpoint`  
**Значения `severity`:** `high` | `medium` | `low`

---

## Версионирование

### GET /protocols/{id}/versions
Список всех версий протокола (без контента — только метаданные).

**Response 200**
```json
[
  {
    "id": "uuid",
    "version": "v0.2",
    "comment": "Исправлена терминология",
    "created_at": "2026-04-23T16:00:00Z"
  },
  {
    "id": "uuid",
    "version": "v0.1",
    "comment": "Первичная генерация",
    "created_at": "2026-04-23T14:30:00Z"
  }
]
```

---

### GET /protocols/{id}/versions/{version_id}
Получить конкретную версию по ID, включая полный контент (FR-06.6 — просмотр любой версии).

**Response 200**
```json
{
  "id": "uuid",
  "version": "v0.1",
  "comment": "Первичная генерация",
  "content": {
    "introduction": "...",
    "objectives": "...",
    "design": "...",
    "population": "...",
    "dosing": "...",
    "efficacy": "...",
    "safety": "...",
    "statistics": "...",
    "ethics": "..."
  },
  "created_at": "2026-04-23T14:30:00Z"
}
```

---

### GET /protocols/{id}/diff
Сравнить две версии протокола (diff по секциям).

**Query params:** `from_version=v0.1&to_version=v0.2`

**Response 200**
```json
{
  "from_version": "v0.1",
  "to_version": "v0.2",
  "sections": {
    "introduction": {
      "changed": true,
      "diff": [
        { "type": "equal", "text": "Пролголимаб (BCD-100) является..." },
        { "type": "delete", "text": "блокатором рецептора PD-1" },
        { "type": "insert", "text": "моноклональным антителом, блокирующим PD-1" }
      ]
    },
    "objectives": {
      "changed": false
    }
  }
}
```

---

## Экспорт

### GET /protocols/{id}/export
Экспортировать протокол.

**Query params:** `format=md|html|docx&version=v0.2`

**Response 200**  
`Content-Type: text/markdown` | `text/html` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document`  
`Content-Disposition: attachment; filename="protocol-v0.2.md"`

---

### GET /protocols/{id}/open-issues
Получить список открытых вопросов для медицинского ревьюера.

**Query params:** `status=open` (по умолчанию), `status=resolved`, `status=wontfix`, `status=all`

**Response 200**
```json
{
  "protocol_title": "Протокол BCD-100 Фаза II",
  "version": "v0.2",
  "issues": [
    {
      "id": "uuid",
      "section": "statistics",
      "issue": "Не определён размер выборки для вторичных конечных точек",
      "status": "open",
      "created_at": "2026-04-23T15:00:00Z",
      "updated_at": "2026-04-23T15:00:00Z"
    }
  ]
}
```

---

### PATCH /protocols/{id}/open-issues/{issue_id}
Обновить статус вопроса (закрыть или отклонить). Действие логируется в `audit_log`.

**Request**
```json
{
  "status": "resolved",
  "resolution_note": "Размер выборки рассчитан в разделе 8.2"
}
```

`status`: `resolved` | `wontfix`  
`resolution_note`: опциональный комментарий (max 500 символов)

**Response 200**
```json
{
  "id": "uuid",
  "section": "statistics",
  "issue": "Не определён размер выборки для вторичных конечных точек",
  "status": "resolved",
  "resolution_note": "Размер выборки рассчитан в разделе 8.2",
  "updated_at": "2026-04-23T16:00:00Z"
}
```

---

## Связанные артефакты (P2 — после MVP)

> **Статус:** отложено. SAP и ICF хранятся в `protocol_versions.content` как ключи `sap` и `icf`.
> Отдельные эндпоинты для их генерации реализуются в рамках Фазы 2 после базового MVP.

### POST /protocols/{id}/generate-artifact
Сгенерировать SAP или ICF на основе текущей версии протокола.

**Request**
```json
{
  "artifact_type": "sap",
  "version_id": "uuid",
  "comment": "Первичная генерация SAP"
}
```

`artifact_type`: `sap` | `icf`

**Response 202**
```json
{
  "task_id": "uuid",
  "status": "pending",
  "artifact_type": "sap"
}
```

> Результат доступен через `GET /protocols/{id}/generate/{task_id}` (тот же polling-механизм).

---

## Утилиты

### GET /biocad-trials
Proxy открытого реестра клинических исследований БИОКАД (`api.biocadless.com`). Нормализует данные.

**Auth:** любая роль  
**Query params:**
- `area` — фильтр по терапевтической области
- `phase` — фильтр по фазе (`I` / `II` / `III` / `IV`)

**Response 200**
```json
{
  "total": 47,
  "source": "api.biocadless.com",
  "records": [
    {
      "title": "BCD-100 Phase II Melanoma",
      "slug": "bcd-100",
      "phase": "II",
      "study_status": "Завершено",
      "recruitment_status": "Набор завершён",
      "nozology": ["Меланома", "Онкология"]
    }
  ]
}
```

**HTTP 504** `UPSTREAM_TIMEOUT` — `api.biocadless.com` не ответил за 15 сек.  
**HTTP 502** `UPSTREAM_ERROR` — ошибка внешнего API.

---

### GET /embeddings/status *(P3 — read-only, all authenticated)*
Проверить статус индексации embeddings: сколько версий проиндексировано и когда последний раз.

**Auth:** Bearer JWT (any role)  
**Response 200**
```json
{
  "indexed_count": 42,
  "total_versions": 55,
  "last_indexed_at": "2026-04-24T10:15:00Z",
  "model": "InHouse/embeddings-model-1",
  "status": "partial"
}
```
**status** может быть: `none` | `partial` | `complete`

---

### POST /embeddings/reindex *(P3 — admin only, RAG)*
Запустить переиндексацию всех версий протоколов для RAG. Генерирует векторные embeddings через AI Gateway.

**Auth:** admin only  
**Response 202**
```json
{ "task_id": "uuid", "queued": 21, "message": "Reindex started in background" }
```

---

### GET /health
Healthcheck для Dokploy.

**Response 200**
```json
{ "status": "ok", "db": "connected", "version": "1.1.0" }
```
