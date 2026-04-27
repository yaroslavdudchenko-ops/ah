import {
  Stack, H1, H2, H3, Text, Grid, Stat, Divider, Pill,
  Card, CardHeader, CardBody, Row, Spacer, Callout, Table,
  useHostTheme
} from 'cursor/canvas';

export default function ProjectSummary() {
  const theme = useHostTheme();
  const t = theme.tokens;

  return (
    <Stack gap={28} style={{ maxWidth: 820, margin: '0 auto', padding: '32px 24px' }}>

      {/* Hero */}
      <Stack gap={6}>
        <H1>AI-генератор протоколов КИ</H1>
        <Text tone="secondary" size="large">
          MVP · FastAPI + React · Dokploy · InHouse/Qwen3.5-122B
        </Text>
      </Stack>

      {/* Stats row */}
      <Grid columns={4} gap={12}>
        <Stat value="137" label="Тестов passed" tone="success" />
        <Stat value="12" label="Разделов протокола" />
        <Stat value="3" label="Роли пользователей" />
        <Stat value="4" label="Формата экспорта" />
      </Grid>

      <Divider />

      {/* What it does */}
      <Stack gap={12}>
        <H2>Что делает система</H2>
        <Text>
          Генерирует полные черновики протоколов клинических исследований на основе
          параметров препарата и терапевтической области. Соответствует GCP ICH E6(R2),
          GCP ЕАЭС, 61-ФЗ.
        </Text>
        <Grid columns={3} gap={12}>
          {[
            ['Ввод параметров', 'Препарат, МНН, фаза I–III, показание, популяция, эндпоинты, критерии'],
            ['AI-генерация', '12 секций + SAP + ICF через внутренний AI Gateway. Fallback при недоступности'],
            ['Экспорт и аудит', 'MD / HTML / DOCX / открытые вопросы CSV. Каждое действие в audit log'],
          ].map(([title, desc]) => (
            <Card key={title} variant="outlined">
              <CardHeader>{title}</CardHeader>
              <CardBody><Text size="small" tone="secondary">{desc}</Text></CardBody>
            </Card>
          ))}
        </Grid>
      </Stack>

      <Divider />

      {/* Tech stack */}
      <Stack gap={12}>
        <H2>Стек</H2>
        <Grid columns={2} gap={12}>
          <Stack gap={8}>
            <H3>Backend</H3>
            <Table
              headers={['Компонент', 'Решение']}
              rows={[
                ['API', 'FastAPI + Python 3.12'],
                ['ORM', 'SQLAlchemy async + asyncpg'],
                ['Миграции', 'Alembic'],
                ['БД', 'PostgreSQL 16'],
                ['LLM', 'InHouse/Qwen3.5-122B (AI Gateway)'],
                ['Тесты', 'pytest-asyncio, httpx, 137 passed'],
              ]}
            />
          </Stack>
          <Stack gap={8}>
            <H3>Frontend</H3>
            <Table
              headers={['Компонент', 'Решение']}
              rows={[
                ['Framework', 'React 18 + TypeScript'],
                ['Сборка', 'Vite'],
                ['Стили', 'Tailwind CSS'],
                ['Роутинг', 'React Router'],
                ['Сервер', 'nginx:alpine'],
                ['Деплой', 'Dokploy (Docker Compose)'],
              ]}
            />
          </Stack>
        </Grid>
      </Stack>

      <Divider />

      {/* Key features */}
      <Stack gap={12}>
        <H2>Ключевые функции</H2>
        <Grid columns={2} gap={10}>
          {[
            ['Генерация', 'Фазы I–III, 12 секций + Appendix SAP/ICF. Section-level перегенерация'],
            ['Fallback', 'При недоступном AI — уникальные шаблоны по каждому разделу с данными протокола'],
            ['Versioning', 'История версий с diff-сравнением. Архивирование старых версий'],
            ['GCP-проверка', 'Автоматическая consistency-проверка по GCP-правилам, открытые вопросы'],
            ['RBAC', 'admin / employee / auditor. Read-only для аудитора, write-lock для одобренных'],
            ['Audit log', 'Каждое действие (create, update, generate, export, check) логируется в БД'],
            ['Экспорт', 'Markdown, HTML, DOCX. Открытые вопросы в JSON/CSV'],
            ['Поиск и теги', 'Полнотекстовый поиск, фильтры по фазе/статусу/области, цветные теги'],
          ].map(([label, desc]) => (
            <Row key={label} gap={10} style={{ alignItems: 'flex-start' }}>
              <Pill tone="info" size="small">{label}</Pill>
              <Text size="small" tone="secondary" style={{ flex: 1 }}>{desc}</Text>
            </Row>
          ))}
        </Grid>
      </Stack>

      <Divider />

      {/* Sessions delivered */}
      <Stack gap={12}>
        <H2>Что сделано за 1.5 дня</H2>
        <Table
          headers={['Сессия', 'Ключевые результаты']}
          rows={[
            ['1–4',  'Архитектура, БД-схема, базовый FastAPI + auth, Alembic миграции'],
            ['5–7',  'AI Gateway интеграция, генератор 12 секций, prompt engineering'],
            ['8–9',  'React UI: создание, просмотр, diff, аудит, экспорт, drag-and-drop теги'],
            ['10',   'RAG Phase 1 (embeddings), 137 тестов, Dokploy-деплой'],
            ['11',   'Фикс fallback-секций, edit-meta UI, отображение exclusion_criteria'],
            ['12',   'SAP/ICF fallbacks, Phase IV удалена, export audit, AI Gateway endpoint fix'],
            ['13',   '5 реальных протоколов BIOCAD (ct.biocad.ru), seed-скрипты, encoding fix'],
            ['14',   'PDF print-стили, canvases в git, CHECKPOINT v14.0.0, RELEASE-NOTES v4.0.0'],
          ]}
        />
      </Stack>

      <Divider />

      {/* Compliance */}
      <Stack gap={12}>
        <H2>Соответствие требованиям</H2>
        <Grid columns={3} gap={10}>
          {[
            ['GCP ICH E6(R2)', 'success'],
            ['GCP ЕАЭС', 'success'],
            ['61-ФЗ', 'success'],
            ['ALCOA++', 'success'],
            ['NFR-08 (no external LLM)', 'success'],
            ['RBAC 3 роли', 'success'],
          ].map(([label, tone]) => (
            <Callout key={label} tone={tone as any}>
              <Text size="small">{label}</Text>
            </Callout>
          ))}
        </Grid>
      </Stack>

      <Divider />

      {/* Deploy */}
      <Stack gap={8}>
        <H2>Деплой</H2>
        <Grid columns={2} gap={12}>
          <Stack gap={6}>
            <H3>Production URL</H3>
            <Text size="small" tone="secondary">
              hgdisgroup123042025-analysisdudchenkoi23-05fc54-10-226-76-173.traefik.me
            </Text>
            <Row gap={8}>
              <Pill tone="success" size="small">frontend healthy</Pill>
              <Pill tone="success" size="small">backend healthy</Pill>
              <Pill tone="success" size="small">db healthy</Pill>
            </Row>
          </Stack>
          <Stack gap={6}>
            <H3>Учётные записи</H3>
            <Table
              headers={['Логин', 'Пароль', 'Роль']}
              rows={[
                ['admin', 'admin123', 'Полный доступ'],
                ['employee', 'emp123', 'Создание и генерация'],
                ['auditor', 'aud123', 'Только чтение'],
              ]}
            />
          </Stack>
        </Grid>
      </Stack>

      <Text tone="secondary" size="small" style={{ marginTop: 8 }}>
        Дедлайн: 24.04.2026 17:30 · Коммит: 8769581 · Тестов: 137 passed
      </Text>

    </Stack>
  );
}
