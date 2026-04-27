import {
  BarChart,
  Button,
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  H3,
  PieChart,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
  useHostTheme,
} from 'cursor/canvas';

// ── Production data · HEAD 5bec271 · 2026-04-27 ─────────────────────────────

const COMMITS = [
  { hash: 'b80014d', date: '24.04 16:44', label: 'feat(session-12)',   note: 'Дедлайн',                                      post: false },
  { hash: '168eeb5', date: '24.04 17:00', label: 'fix(ai-gateway)',    note: 'remove hardcoded /v1 prefix',                  post: true  },
  { hash: '8769581', date: '24.04 17:18', label: 'fix(login)',         note: 'emp123 / aud123',                              post: true  },
  { hash: '5ed5464', date: '26.04',       label: 'feat(seed)',         note: 'seed scripts, BIOCAD patch, PROJECT-SUMMARY',  post: true  },
  { hash: 'c387a84', date: '26.04',       label: 'fix(frontend)',      note: 'cancelled flag, location.replace on 401',      post: true  },
  { hash: 'a68cf57', date: '26.04',       label: 'feat(seed)',         note: '5 реальных протоколов ct.biocad.ru',           post: true  },
  { hash: '8f249e3', date: '26.04',       label: 'docs(checkpoint)',   note: 'v14.0.0 — сессия 14, 37 протоколов в проде',  post: true  },
  { hash: 'c9c51c5', date: '26.04',       label: 'fix(encoding)',      note: 'CP1251/BOM → UTF-8 для 6 файлов docs/',       post: true  },
  { hash: 'da2083f', date: '27.04',       label: 'docs',               note: 'PROJECT-SUMMARY + RELEASE-NOTES обновлены',   post: true  },
  { hash: '5bec271', date: '27.04',       label: 'docs',               note: 'уточнение: 15 протоколов на сайте vs ~37 в БД', post: true },
  { hash: '4173ed3', date: '27.04',       label: 'feat(canvases)',     note: 'canvases/ в репо + PDF print-стили DraftModal', post: true },
];

const BY_AREA = [
  { label: 'Онкология',     value: 17 },
  { label: 'Ревматология',  value: 6  },
  { label: 'Неврология',    value: 5  },
  { label: 'Гематология',   value: 4  },
  { label: 'Прочее',        value: 5  },
];

const BY_STATUS = [
  { label: 'Generated',  value: 26 },
  { label: 'Approved',   value: 5  },
  { label: 'Draft',      value: 4  },
  { label: 'In Review',  value: 2  },
];

const BY_PHASE = [
  { label: 'Фаза I',   value: 6  },
  { label: 'Фаза II',  value: 11 },
  { label: 'Фаза III', value: 16 },
  { label: 'Фаза IV',  value: 4  },
];

const PROD_PROTOCOLS = [
  ['BCD-267-2/VERITAS',   'РМЖ HER2+',              'III', 'Набор открыт',   'ct.biocad.ru (реальные данные)'],
  ['BCD-225-2',           'Рак мочевого пузыря',     'II',  'Набор открыт',   'ct.biocad.ru (реальные данные)'],
  ['BCD-180-4',           'Анкилоз. спондилит',      'I',   'Набор открыт',   'ct.biocad.ru (реальные данные)'],
  ['BCD-283-1',           'Лимфома Ходжкина',         'III', 'Набор завершен', 'ct.biocad.ru (реальные данные)'],
  ['BCD-132-6/AQUARELLE', 'Болезнь Девика / ЗСОНМ',  'I',   'Набор завершен', 'ct.biocad.ru (реальные данные)'],
  ['BCD-281-2/MUSCAT',    'Неврология',               'II',  'Набор открыт',   'seed_10_protocols (синтетика)'],
  ['BCD-100 … BCD-132',   'Различные (демо)',          'I–III','Mixed',         'seed_demo + seed_from_biocad_api'],
];

const SERVICES = [
  ['frontend', 'nginx:alpine :80',      'healthy', 'React 18 + Vite + Tailwind'],
  ['backend',  'python:3.12-slim :8000','healthy', 'FastAPI + SQLAlchemy async'],
  ['db',       'postgres:16-alpine',    'healthy', 'PostgreSQL 16, JSONB'],
];

const DOCS = [
  ['CHECKPOINT.md',        '14.0.0', '2026-04-26'],
  ['RELEASE-NOTES.md',     '4.0.0',  '2026-04-27'],
  ['PROJECT-SUMMARY.md',   '—',      '2026-04-27'],
  ['VERSIONS.md',          '1.7.0',  '2026-04-26'],
  ['test-plan.md',         '3.3.0',  '2026-04-24'],
  ['api-spec.md',          '1.6.0',  '2026-04-24'],
  ['ARCHITECTURE.md',      '1.2.0',  '2026-04-23'],
  ['manual-test-guide.md', '1.2.0',  '2026-04-24'],
];

export default function SynthiaProductionStatus() {
  const { tokens: t } = useHostTheme();

  return (
    <Stack gap={24} style={{ padding: 24, maxWidth: 1100, margin: '0 auto' }}>

      {/* Header + PDF */}
      <Row justify="space-between" align="center">
        <Stack gap={4}>
          <H1>Synthia — Production Status</H1>
          <Text tone="secondary" size="small">
            AI Protocol Generator · Dokploy Production · HEAD: 4173ed3 · 2026-04-27
          </Text>
        </Stack>
        <Button variant="secondary" onClick={() => window.print()}>
          Печать / PDF
        </Button>
      </Row>

      <Callout tone="warning">
        POST-DEADLINE: 11 коммитов после 24.04.2026 17:30 (b80014d). Дедлайн-коммит: b80014d.
        Rollback — CHECKPOINT.md §17.
      </Callout>

      <Callout tone="info">
        На production-сайте: 15 протоколов. В БД всего: ~37 записей (включая локальные seed-данные,
        не все скрипты запускались на проде). Для презентации релевантны 15 видимых на сайте.
      </Callout>

      {/* KPI */}
      <Grid columns={4} gap={12}>
        <Stat value="15"  label="Протоколов на сайте (прод)" tone="success" />
        <Stat value="137" label="Автотестов passed"           tone="success" />
        <Stat value="3"   label="Сервиса (frontend/back/db)"  tone="success" />
        <Stat value="11"  label="Коммитов после дедлайна"     tone="warning" />
      </Grid>

      <Divider />

      {/* Production services */}
      <H2>Сервисы в продакшне (Dokploy)</H2>
      <Table
        headers={['Сервис', 'Образ / Порт', 'Health', 'Описание']}
        rows={SERVICES}
        rowTone={['success', 'success', 'success'] as any}
      />
      <Text tone="secondary" size="small">
        URL: hgdisgroup123042025-analysisdudchenkoi23-05fc54-10-226-76-173.traefik.me
      </Text>
      <Text tone="secondary" size="small">
        * 15 протоколов видны на production-сайте. ~37 записей в БД суммарно (включая локальные seed-данные — не все скрипты запускались на проде).
      </Text>

      <Divider />

      {/* Protocol distribution */}
      <H2>Распределение 37 протоколов</H2>
      <Grid columns={3} gap={16}>
        <Stack gap={6}>
          <H3>По области</H3>
          <BarChart
            categories={BY_AREA.map(d => d.label)}
            series={[{ name: 'Протоколов', data: BY_AREA.map(d => d.value) }]}
            height={170}
          />
        </Stack>
        <Stack gap={6}>
          <H3>По статусу</H3>
          <PieChart data={BY_STATUS.map(d => ({ label: d.label, value: d.value }))} height={170} />
        </Stack>
        <Stack gap={6}>
          <H3>По фазе</H3>
          <BarChart
            categories={BY_PHASE.map(d => d.label)}
            series={[{ name: 'Протоколов', data: BY_PHASE.map(d => d.value) }]}
            height={170}
          />
        </Stack>
      </Grid>

      <Grid columns={3} gap={12}>
        <Stat value="~9"  label="Набор открыт (прод)"    tone="success" />
        <Stat value="~6"  label="Набор завершен (прод)"  />
        <Stat value="~37" label="Записей в БД (итого)"   tone="warning" />
      </Grid>

      <Divider />

      {/* Key protocols */}
      <H2>Ключевые протоколы (прод)</H2>
      <Table
        headers={['Препарат', 'Нозология', 'Фаза', 'Набор', 'Источник']}
        rows={PROD_PROTOCOLS}
        rowTone={[
          'success','success','success','success','success',
          'warning','default',
        ] as any}
      />

      <Divider />

      {/* Git history */}
      <H2>Git-история (с дедлайна)</H2>
      <Table
        headers={['Хэш', 'Дата', 'Коммит', 'Описание', 'Статус']}
        rows={COMMITS.map(c => [
          c.hash, c.date, c.label, c.note,
          c.post ? 'POST-DEADLINE' : 'Deadline',
        ])}
        rowTone={COMMITS.map(c => (c.post ? 'warning' : 'success')) as any}
      />

      <Divider />

      {/* Tech stack */}
      <H2>Технический стек</H2>
      <Grid columns={2} gap={16}>
        <Table
          headers={['Backend', 'Версия/Решение']}
          rows={[
            ['Python', '3.12-slim'],
            ['FastAPI', 'async + BackgroundTasks'],
            ['SQLAlchemy', '2.x async + asyncpg'],
            ['Alembic', 'миграции 001–005'],
            ['AI Gateway', 'InHouse/Qwen3.5-122B'],
            ['RAG', 'Phase 1: JSONB embeddings (UI — backlog)'],
            ['Тесты', 'pytest 137/137 passed'],
          ]}
        />
        <Table
          headers={['Frontend / Infra', 'Версия/Решение']}
          rows={[
            ['React', '18 + TypeScript + Vite'],
            ['Tailwind CSS', '3.x'],
            ['React Router', 'v6'],
            ['nginx', 'alpine (SPA fallback + /api proxy)'],
            ['Dokploy', 'Docker Compose mode'],
            ['Traefik', 'ingress (auto-labels)'],
            ['PostgreSQL', '16-alpine, JSONB'],
          ]}
        />
      </Grid>

      <Divider />

      {/* RBAC */}
      <H2>Роли и доступ</H2>
      <Table
        headers={['Логин', 'Пароль', 'Права']}
        rows={[
          ['admin',    'admin123', 'CRUD + Delete + Approve (любой протокол)'],
          ['employee', 'emp123',   'Create / Read / Update / Generate. Нет Delete, нет self-approve'],
          ['auditor',  'aud123',   'Read only + Audit Trail. Нет редактирования'],
        ]}
      />

      <Divider />

      {/* Docs */}
      <H2>Документация</H2>
      <Table
        headers={['Документ', 'Версия', 'Дата']}
        rows={DOCS}
      />

      <Divider />

      <Row justify="space-between" align="center">
        <Text tone="secondary" size="small">
          Synthia AI Protocol Generator · CHECKPOINT v14.0.0 · HEAD: 4173ed3 · GitLab + GitHub origin/master
        </Text>
        <Button variant="ghost" onClick={() => window.print()}>
          Печать / PDF
        </Button>
      </Row>

    </Stack>
  );
}
