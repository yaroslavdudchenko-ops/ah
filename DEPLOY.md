# Руководство по деплою на Dokploy

**Version:** 1.0.0 | **Date:** 2026-04-23 | **Status:** Draft

---

## 1. Сервисы

| Сервис | Образ | Порт | Описание |
|---|---|---|---|
| `frontend` | nginx:alpine (статика React) | 80 | SPA + reverse proxy /api → backend |
| `backend` | python:3.12-slim (сборка) | 8000 | FastAPI REST API |
| `db` | postgres:16-alpine | 5432 | PostgreSQL, данные в named volume |

---

## 2. Переменные окружения

| Переменная | Тип | Пример | Описание |
|---|---|---|---|
| `AI_GATEWAY_URL` | required | `https://ai-gateway.internal/v1` | URL внутреннего AI Gateway |
| `AI_GATEWAY_API_KEY` | required | `gw-key-...` | API ключ AI Gateway |
| `AI_GATEWAY_MODEL` | optional | `InHouse/Qwen3.5-122B` | Модель LLM (только локальные) |
| `POSTGRES_PASSWORD` | required | `s3cr3t` | Пароль PostgreSQL |
| `POSTGRES_USER` | optional | `app` | Пользователь PostgreSQL (по умолчанию: app) |
| `POSTGRES_DB` | optional | `protocols` | Имя базы данных (по умолчанию: protocols) |
| `DATABASE_URL` | required | `postgresql+asyncpg://app:pass@db:5432/protocols` | Строка подключения для SQLAlchemy |
| `CORS_ORIGINS` | optional | `http://localhost` | Разрешённые CORS origins |
| `LOG_LEVEL` | optional | `info` | Уровень логирования: `debug` / `info` / `warning` / `error` |
| `APP_ENV` | optional | `development` | Окружение: `development` / `staging` (не использовать `production`) |

---

## 3. Volumes и persistent data

| Volume | Сервис | Путь в контейнере | Содержимое |
|---|---|---|---|
| `db-data` | db | `/var/lib/postgresql/data` | Данные PostgreSQL (протоколы, версии, шаблоны) |

**Backup:** Dokploy поддерживает Volume Backups только для named volumes. Настраивается через вкладку **Volumes** в интерфейсе Dokploy.

> `./` относительные пути в volumes использовать нельзя — Dokploy делает `git clone` при каждом деплое, очищая рабочую директорию.

---

## 4. Healthcheck-и

| Сервис | Эндпоинт | Ожидаемый ответ | Интервал |
|---|---|---|---|
| `backend` | `GET /health` | `{"status": "ok"}` | 30s / timeout 5s |
| `db` | `pg_isready -U app` | exit 0 | 30s / timeout 5s |
| `frontend` | `GET /` | HTTP 200 | 30s / timeout 5s |

---

## 5. Локальный запуск

```bash
# 1. Клонируй репозиторий
git clone https://github.com/<username>/research-protocol-generator.git
cd research-protocol-generator

# 2. Заполни переменные
cp .env.example .env
# Открой .env и задай OPENROUTER_API_KEY и POSTGRES_PASSWORD

# 3. Запуск
docker compose up --build

# Симуляция Dokploy (env -i как в production деплое)
env -i PATH="$PATH" docker compose up --build
```

Приложение: `http://localhost:80`  
API docs (Swagger): `http://localhost:8000/docs`

---

## 6. Деплой в Dokploy

### 6.1 Подключение репозитория

Репозиторий подключается администратором через Git-провайдер. После выдачи прав пользователь видит проект в дашборде.

> **НЕ нажимай "Disconnect Repository"** — восстановить может только администратор.

### 6.2 Переменные окружения в UI

1. Открой сервис → вкладка **Environment**
2. Добавь переменные из таблицы в разделе 2 (формат `KEY=value`)
3. Нажми **Save**

Минимально для старта:
```
OPENROUTER_API_KEY=sk-or-v1-...
POSTGRES_PASSWORD=your_password
DATABASE_URL=postgresql+asyncpg://app:your_password@db:5432/protocols
```

### 6.3 Isolated Deployment (рекомендуется)

1. Сервис → вкладка **Advanced**
2. Включи **Enable Isolated Deployment**
3. **Save** → **General** → **Deploy**

### 6.4 Настройка домена

**Для тестирования (HTTP):**
1. Вкладка **Domains** → **Add Domain**
2. **Service Name:** `frontend`
3. Нажми 🎲 для генерации адреса `*.traefik.me`
4. **Container Port:** `80`
5. **Create/Update** → **Deploy**

**Для HTTPS:** создай заявку в DevOps на DNS-запись, затем добавь домен с включённым HTTPS.

### 6.5 Запуск деплоя

Вкладка **General** → кнопка **Deploy**

Статус и логи сборки: вкладка **Deployments** → **View**

### 6.6 Терминал контейнера

Вкладка **General** → **Open Terminal** — доступ к shell внутри контейнера.

---

## 7. Troubleshooting

| Симптом | Причина | Решение |
|---|---|---|
| Деплой упал: `required variable not set` | Не задана обязательная переменная | Environment → добавить переменную → Deploy |
| Домен не открывается после деплоя | Traefik labels применяются только при деплое | Нажать Deploy после изменения домена |
| Данные пропали после деплоя | Использовались `./` пути в volumes | Заменить на named volumes (`db-data`) |
| Backend недоступен с frontend | Nginx proxy config неверный | Проверить `nginx.conf`: `proxy_pass http://backend:8000` |
| `connection refused` на DB | DB не успела запуститься | Добавить `depends_on: db: condition: service_healthy` |
| Healthcheck не проходит | `/health` возвращает не 200 | Проверить backend: `GET /health` должен вернуть `{"status": "ok"}` |

---

## 8. Ресурсные лимиты (рекомендуемые)

| Сервис | CPU | Memory | Примечание |
|---|---|---|---|
| `frontend` | 0.1 CPU | 64 MB | nginx статика, нагрузка минимальная |
| `backend` | 0.5 CPU | 512 MB | FastAPI + AI вызовы, может быть пиковая нагрузка |
| `db` | 0.5 CPU | 256 MB | PostgreSQL для MVP с малым числом пользователей |

Изменение лимитов запрашивается у платформенного администратора.
