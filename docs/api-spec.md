# REST API Specification

**Version:** 1.2.0 | **Date:** 2026-04-23 | **Status:** Draft  
**Author:** System Architect  
**Standards:** CRUDL (полное покрытие операций для каждой сущности), ALCOA++

Base URL: `/api/v1`  
Content-Type: `application/json`

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
Список протоколов.

**Query params:** `page=1&size=20`

**Response 200**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "...",
      "phase": "II",
      "indication": "...",
      "status": "draft",
      "updated_at": "..."
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
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

### GET /health
Healthcheck для Dokploy.

**Response 200**
```json
{ "status": "ok", "db": "connected", "version": "1.0.0" }
```
