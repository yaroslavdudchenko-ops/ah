# A-011: Test Plan — AI Protocol Generator

**Version:** 2.0.0 | **Date:** 2026-04-23 | **Status:** Active  
**Artifact ID:** A-011  
**Стандарт:** IEEE 829, ISTQB Foundation Level

---

## 1. Scope

Тестирование MVP (v0.1.0) AI-генератора протоколов клинических исследований.

| Тип тестирования | Инструмент | Фаза |
|---|---|---|
| Unit-тесты backend | pytest + pytest-asyncio | Фаза 2.5 (автомат) |
| Integration-тесты backend | pytest + httpx.AsyncClient | Фаза 2.5 (автомат) |
| API smoke-тесты | `smoke_test.http` (REST Client) | Фаза 1.5 |
| Ручное функциональное | Чеклист ниже | Фаза 2.5 |
| E2E (Happy Path) | Ручной прогон | Фаза 2.5 |
| Регрессионный | Чеклист перед сдачей | Перед деплоем |

---

## 2. Тестовые окружения

| Окружение | URL | Условие запуска |
|---|---|---|
| Local backend | `http://localhost:8000` | `docker compose up --build` |
| Local frontend | `http://localhost:80` | `docker compose up --build` |
| Swagger UI | `http://localhost:8000/docs` | автоматически при старте backend |
| Staging (Dokploy) | `https://*.traefik.me` | после деплоя |

---

## 3. Демо-данные

### Dataset-1: Фаза II, Онкология (BCD-100)

```json
{
  "title": "BCD-100 Phase II Study in Metastatic Melanoma",
  "drug_name": "BCD-100",
  "inn": "Пролголимаб",
  "phase": "II",
  "therapeutic_area": "oncology",
  "indication": "Метастатическая меланома, прогрессия после 1 линии терапии",
  "population": "Взрослые ≥18 лет, ECOG 0-1, гистологически верифицированная меланома",
  "primary_endpoint": "ORR (Objective Response Rate) по RECIST 1.1",
  "secondary_endpoints": ["PFS", "OS", "DoR", "DCR"],
  "duration_weeks": 96,
  "dosing": "1 мг/кг в/в каждые 2 недели",
  "inclusion_criteria": [
    "Возраст ≥18 лет",
    "ECOG PS 0-1",
    "Гистологически верифицированная меланома",
    "Наличие измеримых очагов по RECIST 1.1"
  ],
  "exclusion_criteria": [
    "Активные аутоиммунные заболевания",
    "Системная иммуносупрессивная терапия",
    "Активные метастазы в ЦНС"
  ]
}
```

### Dataset-2: Фаза III, Дерматология (BCD-089)

```json
{
  "title": "BCD-089 Phase III RCT in Moderate-to-Severe Psoriasis",
  "drug_name": "BCD-089",
  "inn": "Биоаналог иксекизумаба",
  "phase": "III",
  "therapeutic_area": "dermatology",
  "indication": "Псориаз среднетяжёлый и тяжёлый (PASI ≥12, BSA ≥10%)",
  "population": "Взрослые ≥18 лет, неадекватный ответ на топическую терапию или фототерапию",
  "primary_endpoint": "PASI 75 на 12 неделе",
  "secondary_endpoints": ["PASI 90", "PASI 100", "IGA 0/1", "DLQI"],
  "duration_weeks": 52,
  "dosing": "160 мг п/к на неделе 0, затем 80 мг п/к каждые 2 недели",
  "inclusion_criteria": [
    "Возраст ≥18 лет",
    "PASI ≥12 и BSA ≥10%",
    "IGA ≥3",
    "Неадекватный ответ на ≥1 стандартную терапию"
  ],
  "exclusion_criteria": [
    "Беременность или кормление грудью",
    "Активный туберкулёз",
    "Тяжёлая почечная недостаточность (СКФ < 30)"
  ]
}
```

---

## 4. Happy Path — основной сценарий

> Полный end-to-end прогон без ошибок. Должен проходить **всегда**.

### HP-01: Полный жизненный цикл протокола (Dataset-1)

| Шаг | Действие | Ожидаемый результат | Приоритет |
|---|---|---|---|
| HP-01.1 | Открыть `http://localhost:80` | Главная страница загружается без ошибок консоли | P0 |
| HP-01.2 | Нажать "+ Новый протокол" | Форма создания открылась, список шаблонов отображается (≥3) | P0 |
| HP-01.3 | Выбрать шаблон "Phase II — Single-Arm" | Шаблон выбран, форма предзаполнена | P0 |
| HP-01.4 | Заполнить форму Dataset-1, нажать "Создать" | Протокол создан, ID получен, статус `draft`, редирект на страницу протокола | P0 |
| HP-01.5 | Нажать "Сгенерировать протокол" | Прогресс-индикатор появился, запрос ушёл | P0 |
| HP-01.6 | Ожидать завершения (≤120 сек) | ≥7 секций отображаются (MVP minimum), статус → `generated` | P0 |
| HP-01.7 | Проверить раздел "Introduction" | Содержит H2 заголовки, упоминает BCD-100/Пролголимаб, нет "стен текста" | P0 |
| HP-01.8 | Проверить раздел "Objectives" | Упоминает ORR как primary endpoint, ICH E6 терминология | P0 |
| HP-01.9 | Проверить раздел "Population" | Упоминает ECOG 0-1, критерии из формы | P0 |
| HP-01.10 | Нажать "Экспорт → Markdown" | Файл `protocol.md` скачан, размер > 0 | P0 |
| HP-01.11 | Открыть .md файл | H1 = название протокола, ≥7 разделов H2, метка "FOR REVIEW ONLY" | P0 |
| HP-01.12 | Нажать "Экспорт → HTML" | Файл `protocol.html` скачан | P0 |
| HP-01.13 | Открыть .html в браузере | Корректный рендеринг, заголовки, нет сломанного HTML | P0 |
| HP-01.14 | Вернуться на главную | Протокол BCD-100 в списке с датой и статусом | P0 |

### HP-02: Второй набор данных (Dataset-2)

| Шаг | Действие | Ожидаемый результат | Приоритет |
|---|---|---|---|
| HP-02.1 | Создать протокол с Dataset-2 | Протокол создан с Phase III | P0 |
| HP-02.2 | Сгенерировать | Секции содержат дерматологическую терминологию: PASI, BSA, IGA | P0 |
| HP-02.3 | Проверить "Design" | Упоминает рандомизацию, плацебо-контроль (Phase III RCT) | P0 |
| HP-02.4 | Экспорт MD | Оба протокола независимы, файлы не перемешиваются | P0 |

---

## 5. Альтернативные сценарии и негативные тесты

### ALT-01: Валидация формы (Frontend)

| ID | Действие | Ожидаемый результат | Приоритет |
|---|---|---|---|
| ALT-01.1 | Отправить пустую форму | Все обязательные поля подсвечены красным, сабмит заблокирован | P0 |
| ALT-01.2 | Ввести `phase = "IV"` (не I/II/III) | Ошибка валидации: "Phase must be I, II, or III" | P0 |
| ALT-01.3 | `duration_weeks = 0` | Ошибка: "Duration must be ≥ 1 week" | P0 |
| ALT-01.4 | `duration_weeks = 999` | Ошибка: "Duration must be ≤ 520 weeks" | P0 |
| ALT-01.5 | `title` = 4 символа (< 5) | Ошибка минимальной длины | P0 |
| ALT-01.6 | `primary_endpoint` = 2 символа | Ошибка: min 3 символа | P0 |
| ALT-01.7 | Вставить XSS: `<script>alert(1)</script>` в title | Текст отображается как строка, скрипт не выполняется | P0 |

### ALT-02: AI Gateway недоступен

| ID | Действие | Ожидаемый результат | Приоритет |
|---|---|---|---|
| ALT-02.1 | Запустить генерацию при недоступном AI Gateway | Секции генерируются с фallback-текстом (template), статус `generated` | P0 |
| ALT-02.2 | Проверить содержимое fallback | Секция содержит `[TEMPLATE FALLBACK — FOR REVIEW ONLY]`, не HTTP 500 | P0 |
| ALT-02.3 | `POST /check` при недоступном AI Gateway | HTTP 200 с `compliance_score: 0`, issue "AI Gateway недоступен" — не 500 | P0 |
| ALT-02.4 | Проверить статус задачи при сбое | `status: "completed"` (fallback), не `"failed"` без причины | P1 |

### ALT-03: Экспорт до генерации

| ID | Действие | Ожидаемый результат | Приоритет |
|---|---|---|---|
| ALT-03.1 | Попытаться экспортировать протокол без сгенерированного контента | HTTP 422 + `{"error": {"code": "NO_CONTENT", ...}}` | P0 |
| ALT-03.2 | UI показывает кнопки экспорта неактивными если нет версий | Кнопки задизейблены, tooltip "Сначала сгенерируйте протокол" | P1 |

### ALT-04: Несуществующий ресурс

| ID | Действие | Ожидаемый результат | Приоритет |
|---|---|---|---|
| ALT-04.1 | `GET /api/v1/protocols/invalid-uuid` | HTTP 404 + `{"error": {"code": "PROTOCOL_NOT_FOUND", ...}}` | P0 |
| ALT-04.2 | `GET /api/v1/protocols/{id}/generate/bad-task-id` | HTTP 404 + `{"error": {"code": "TASK_NOT_FOUND", ...}}` | P0 |
| ALT-04.3 | `GET /api/v1/templates/nonexistent` | HTTP 404 + `{"error": {"code": "TEMPLATE_NOT_FOUND", ...}}` | P0 |

### ALT-05: P2 заглушки

| ID | Действие | Ожидаемый результат | Приоритет |
|---|---|---|---|
| ALT-05.1 | `GET /api/v1/protocols/{id}/diff?v1=1&v2=2` | HTTP 501 + `{"error": {"code": "NOT_IMPLEMENTED", ...}}` | P1 |
| ALT-05.2 | `POST /api/v1/templates` (создание шаблона) | HTTP 501 + `{"error": {"code": "NOT_IMPLEMENTED", ...}}` | P1 |
| ALT-05.3 | `GET /export?format=docx` (если заглушка) | HTTP 501, не 500 | P2 |

### ALT-06: Граничные значения данных

| ID | Действие | Ожидаемый результат | Приоритет |
|---|---|---|---|
| ALT-06.1 | Создать протокол с 20 критериями исключения | Создан успешно, все 20 сохранены | P1 |
| ALT-06.2 | Indication = 1000 символов | Создан успешно | P1 |
| ALT-06.3 | Пустой список `secondary_endpoints: []` | Создан успешно, генерация работает | P1 |
| ALT-06.4 | Drug name со спецсимволами: `BCD-100/Аналог (тест)` | Создан успешно, спецсимволы сохранены | P1 |

### ALT-07: Повторная генерация (версионирование)

| ID | Действие | Ожидаемый результат | Приоритет |
|---|---|---|---|
| ALT-07.1 | Сгенерировать протокол дважды | Создано 2 версии (v1, v2), обе доступны через `/versions` | P1 |
| ALT-07.2 | `GET /protocols/{id}/versions` | Список из 2 версий, упорядочен по version_number | P1 |
| ALT-07.3 | `GET /protocols/{id}/versions/{vid}` | Конкретная версия с полным content | P1 |

### ALT-08: Удаление протокола

| ID | Действие | Ожидаемый результат | Приоритет |
|---|---|---|---|
| ALT-08.1 | `DELETE /api/v1/protocols/{id}` | HTTP 204, протокол удалён | P0 |
| ALT-08.2 | `GET /api/v1/protocols/{id}` после удаления | HTTP 404 | P0 |
| ALT-08.3 | `/versions` удалённого протокола | HTTP 404 (cascade) | P1 |

---

## 6. Автоматические тесты (pytest)

### Структура

```
backend/tests/
  conftest.py              # fixtures: db session, async client, mock AI
  test_health.py           # GET /health
  test_protocols.py        # CRUDL + валидация
  test_generate.py         # генерация + статус задачи
  test_check.py            # consistency check
  test_export.py           # MD, HTML, DOCX
  test_templates.py        # шаблоны
  test_ai_gateway.py       # unit: retry, fallback, timeout
  test_generator.py        # unit: секции, контексты
  test_export_service.py   # unit: MD/HTML структура
  smoke_test.http          # REST Client E2E (ручной запуск)
```

### Запуск

```bash
# Все тесты
docker compose exec backend pytest tests/ -v

# Только unit (без DB)
docker compose exec backend pytest tests/ -v -m unit

# Только интеграционные
docker compose exec backend pytest tests/ -v -m integration

# С coverage
docker compose exec backend pytest tests/ --cov=app --cov-report=term-missing
```

### Покрытие — минимальный порог

| Модуль | Минимум coverage |
|---|---|
| `services/ai_gateway.py` | 90% |
| `services/generator.py` | 85% |
| `services/export_service.py` | 80% |
| `routers/protocols.py` | 80% |
| `routers/generate.py` | 75% |

---

## 7. Критерии приёмки (Definition of Done)

### P0 — обязательно для сдачи

- [ ] HP-01.1..HP-01.14 — полный happy path пройден на Dataset-1
- [ ] HP-02.1..HP-02.4 — happy path пройден на Dataset-2
- [ ] ALT-01.1..ALT-01.3 — базовая валидация работает
- [ ] ALT-02.1..ALT-02.3 — AI Gateway fallback без 500
- [ ] ALT-03.1 — export before generate → 422
- [ ] ALT-04.1..ALT-04.3 — 404 на несуществующие ресурсы
- [ ] `GET /health` → `{"status":"ok","db":"connected"}`
- [ ] Swagger UI (`/docs`) доступен и содержит все эндпоинты
- [ ] Приложение доступно по публичному Dokploy URL
- [ ] Нет HTTP 500 в Happy Path

### P1 — важно

- [ ] ALT-05.1..ALT-05.2 — P2 stubs возвращают 501 (не 500)
- [ ] ALT-07.1..ALT-07.3 — версионирование работает
- [ ] pytest unit-тесты проходят без ошибок

### P2 — усиление

- [ ] ALT-06.1..ALT-06.4 — граничные значения
- [ ] ALT-08.3 — cascade delete
- [ ] Coverage ≥ 80% по всем модулям
- [ ] Playwright E2E HP-01 (автоматизированный)

---

## 8. Регрессионный чеклист перед сдачей

```
[ ] docker compose up --build — все 3 контейнера Green
[ ] GET /health → 200 {"status":"ok","db":"connected"}
[ ] Swagger UI /docs открывается
[ ] Создать BCD-100 (Dataset-1) через UI
[ ] Сгенерировать — ≥7 секций появились
[ ] Экспорт MD — файл скачан, содержит BCD-100
[ ] Экспорт HTML — открывается в браузере корректно
[ ] Создать BCD-089 (Dataset-2) — независимый протокол
[ ] Список протоколов — оба отображаются
[ ] Нет 500 в docker compose logs
[ ] Нет ошибок в консоли браузера
[ ] Публичный URL доступен
[ ] README содержит инструкцию запуска
[ ] PROMPTS.md содержит ≥3 реальные итерации
```
