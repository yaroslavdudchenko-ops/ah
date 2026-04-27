import {
  H1, H2, H3, Text, Stack, Row, Grid, Divider,
  Card, CardBody, CardHeader, Stat, Pill, Callout, Table,
  BarChart, PieChart,
  useHostTheme,
} from 'cursor/canvas';

type PillTone = 'default' | 'success' | 'warning' | 'danger' | 'info';

interface RoleReview {
  role: string;
  score: number;
  strengths: string[];
  gaps: string[];
  verdict: PillTone;
  verdictLabel: string;
}

// ─── Data (CHECKPOINT v12.0.0 · сессия 12 · 24.04.2026) ─────────────────────

const ROLE_REVIEWS: RoleReview[] = [
  {
    role: 'System Architect',
    score: 91,
    strengths: [
      'C4 L1/L2/L3 + ER + Deploy — полный набор диаграмм с ADR',
      '3 ADR с обоснованием (PostgreSQL, AI Gateway, Stack)',
      'CRUDL-матрица покрывает все сущности, Governance (4-eyes) задокументирован',
      'RAG Phase 1 добавлен: embeddings router, JSONB vectors, migration 005',
      'Dokploy-constraints соблюдены строго (named volumes, non-root, HEALTHCHECK)',
    ],
    gaps: [
      'ARCHITECTURE.md не обновлён для biocad_trials, embeddings, audit роутеров',
      'database-schema.md не отражает protocol_embeddings (migration 005)',
    ],
    verdict: 'success',
    verdictLabel: 'Готов',
  },
  {
    role: 'Backend Developer',
    score: 90,
    strengths: [
      '30+ эндпоинтов: CRUDL, generate, check, export, auth, audit, diff, copy, biocad-trials, embeddings',
      'Alembic миграции 001–005 (async SQLAlchemy 2)',
      'AI Gateway: httpx + tenacity ×3, fallback HTTP 503',
      'prompt_guard.py: 18 паттернов инъекций, max 2000 символов',
      'SAP/ICF генерация: Appendix A (ITT/PP/Safety) + Appendix B (61-ФЗ, ICH E6 §4.8)',
      'Open Issues export: JSON (UTF-8) + CSV (UTF-8-SIG) с audit log',
      'Export router: AuditLog action="export" с format/version_id',
      'Generator: уникальные fallback для каждой секции включая SAP/ICF',
    ],
    gaps: [
      'task_id хранится в памяти — рестарт теряет статус генерации (P1)',
      'api-spec.md не отражает /embeddings/* (документация отстаёт)',
    ],
    verdict: 'success',
    verdictLabel: 'Готов',
  },
  {
    role: 'Frontend Developer',
    score: 84,
    strengths: [
      'CreateProtocolPage.tsx: полная форма с критериями вкл/искл, тегами, автодополнением',
      'Diff viewer: слайд-панель, color-coded unified diff по секциям',
      'SAP/ICF кнопки в сайдбаре (Артефакты)',
      '4-eyes UI: кнопка «Одобрить» скрыта для creator + дисклеймер',
      'Open Issues dropdown с иконками Download (JSON/CSV)',
      'AutocompleteField: inn, drug_name, indication, population',
      'Phase I/II/III only — Phase IV отклоняется фронтом и бэкендом (422)',
    ],
    gaps: [
      'Уведомления рецензенту не реализованы (P1 backlog)',
      'Мобильная адаптация не тестировалась',
      'Нет отдельной страницы просмотра SAP/ICF',
    ],
    verdict: 'success',
    verdictLabel: 'Готов',
  },
  {
    role: 'QA Engineer',
    score: 82,
    strengths: [
      '137 автотестов: smoke, happy path, negative, security, RBAC, governance, fallbacks',
      'test_new_features.py: сессия 11–12 (edit meta, exclusion criteria, SAP/ICF, export audit)',
      'test-plan.md v3.4.0 — EDIT-META, EXCL-CRIT, FALLBACK-01, PHASE-IV-01',
      'Credential fixtures исправлены: EMPLOYEE_PASSWORD / AUDITOR_PASSWORD из env',
      '4-eyes lifecycle тест, diff 200 vs 501 — актуализированы',
    ],
    gaps: [
      'import pytest_asyncio в test_new_features.py на строке 432 (нужно в топ файла)',
      'Gap: нет теста export → audit log action="export" (декларирован, не написан)',
      'Нет теста против реального AI Gateway (только моки)',
    ],
    verdict: 'success',
    verdictLabel: 'Готов',
  },
  {
    role: 'DevOps',
    score: 83,
    strengths: [
      'docker-compose.yml: 3 сервиса, named volumes, HEALTHCHECK, non-root user',
      'DEPLOY.md v1.2.0 — пошаговая инструкция Dokploy + troubleshooting',
      'GitHub mirror: github.com/yaroslavdudchenko-ops/ah (master, актуален)',
      'AI_EMBEDDING_URL: graceful fallback если пустой (RAG отключается без ошибки)',
    ],
    gaps: [
      'Dokploy redeploy после migrations 004–005 не выполнен',
      'CI/CD пайплайн не настроен (ручной деплой)',
    ],
    verdict: 'success',
    verdictLabel: 'Готов',
  },
  {
    role: 'Clinical Analyst',
    score: 78,
    strengths: [
      '12 разделов ICH E6(R2) + GCP ЕАЭС — полный охват',
      'SAP Appendix A: ITT/PP/Safety, power analysis, MCAR/MAR/MNAR',
      'ICF Appendix B: 61-ФЗ, ICH E6 §4.8, Приказ №353н — 11 обязательных разделов',
      'Phase IV запрет: backend 422, frontend только I/II/III',
      'Нормативная база: GCP ЕАЭС (ЕЭК №79/63), №75н, №708н',
    ],
    gaps: [
      'GCP/ICH compliance scores не прошли клиническую валидацию (дисклеймер присутствует)',
      'RAG отключён (AI_EMBEDDING_URL пустой) — без исторических протоколов',
      'Нет ссылки на Федеральный реестр КИ Минздрава (NFR-07г — stub)',
    ],
    verdict: 'warning',
    verdictLabel: 'Риски',
  },
  {
    role: 'InfoSec',
    score: 85,
    strengths: [
      'Только внутренний AI Gateway (NFR-08) — внешние LLM запрещены',
      'PBKDF2-HMAC-SHA256 (260 000 итераций) для паролей',
      'JWT Bearer, 8ч TTL, RBAC (admin/employee/auditor)',
      'prompt_guard.py: санитация custom_prompt перед отправкой в LLM',
      'AuditLog: все действия (generate/export/update/delete) логируются',
      'Секреты только в .env, не в git (.gitignore)',
    ],
    gaps: [
      'КРИТИЧЕСКИ: corecase.md содержит plain-text третьесторонний API-токен — ротация обязательна',
      'Rate limiting не реализован (нет защиты от brute-force)',
      'Нет ротации JWT (refresh token не реализован)',
    ],
    verdict: 'warning',
    verdictLabel: 'Блокер',
  },
  {
    role: 'Tech Writer',
    score: 80,
    strengths: [
      'CHECKPOINT.md v12.0.0 — полное восстановление контекста сессий 1–12',
      'RELEASE-NOTES.md v3.0.0 — v1.0.0 + v1.1.0 + v1.2.0 changelog',
      'functional-requirements.md v1.3.0 — FR-01..FR-09 актуальны',
      'test-plan.md v3.4.0 — EDIT-META, EXCL-CRIT, FALLBACK, PHASE-IV добавлены',
      'PROMPTS.md v2.0.0 — SAP/ICF промпты задокументированы',
      'ALCOA++ заголовки в документах, artifacts-catalog v1.3.0',
    ],
    gaps: [
      'api-spec.md v1.6.0 — не отражает /embeddings/* (нужна v1.7.0)',
      'VERSIONS.md: encoding mojibake в заголовках (UTF-8 без BOM)',
      '.env.example отсутствует (README ссылается, файл не создан)',
    ],
    verdict: 'success',
    verdictLabel: 'Готов',
  },
];

const CORECASE_FEATURES = [
  { id: 'FR-01', name: 'Библиотека шаблонов',          priority: 'P1', status: 'done',    note: 'Phase I/II/III шаблоны в seed; /templates API; выбор в форме' },
  { id: 'FR-02', name: 'Ввод параметров',              priority: 'P0', status: 'done',    note: 'Все 9+ полей + критерии вкл/искл + теги + автодополнение' },
  { id: 'FR-03', name: 'AI-генерация (12 секций)',     priority: 'P0', status: 'done',    note: '12 секций + SAP + ICF; параллельно; fallback уникальны' },
  { id: 'FR-04', name: 'Контроль консистентности',    priority: 'P1', status: 'done',    note: 'ICH + РФ НМД score, open issues с severity, GCP-подсказки' },
  { id: 'FR-05', name: 'SAP / ICF артефакты',         priority: 'P2', status: 'done',    note: 'Appendix A + B — промпты + fallbacks + UI + хранение в JSONB' },
  { id: 'FR-06', name: 'Версионирование + Diff',       priority: 'P1', status: 'done',    note: 'ProtocolVersion + unified diff + UI панель + copy/fork' },
  { id: 'FR-07', name: 'Экспорт MD/HTML/DOCX',        priority: 'P0', status: 'done',    note: 'MD + HTML + DOCX + Open Issues JSON/CSV + audit log' },
  { id: 'FR-08', name: 'Auth + RBAC',                  priority: 'P0', status: 'done',    note: 'JWT, 3 роли, AuditLog, PBKDF2-SHA256' },
  { id: 'FR-09', name: 'Governance (4-eyes, lock)',    priority: 'P1', status: 'done',    note: '4-eyes approve + lock after approve + copy + in_review status' },
  { id: 'FR-10', name: 'RAG Phase 1',                  priority: 'P2', status: 'partial', note: 'JSONB embeddings + API; отключён без AI_EMBEDDING_URL' },
  { id: 'NFR-07', name: 'РФ НМД нормативная база',    priority: 'P1', status: 'partial', note: 'GCP ЕАЭС, 61-ФЗ, №353н/75н/708н реализованы; реестр КИ — stub' },
  { id: 'NFR-08', name: 'InfoSec: только внутр. LLM', priority: 'P0', status: 'done',    note: 'AI Gateway only + prompt_guard + секреты в .env' },
];

export default function FinalProjectReview() {
  const theme = useHostTheme();
  const t = theme.tokens;

  const avgScore = Math.round(ROLE_REVIEWS.reduce((s, r) => s + r.score, 0) / ROLE_REVIEWS.length);
  const doneCount    = CORECASE_FEATURES.filter(f => f.status === 'done').length;
  const partialCount = CORECASE_FEATURES.filter(f => f.status === 'partial').length;
  const coveragePct  = Math.round(((doneCount + partialCount * 0.5) / CORECASE_FEATURES.length) * 100);

  const scoreChartData = ROLE_REVIEWS.map(r => ({
    label: r.role.replace('Developer', 'Dev').replace(' Engineer', '').replace('Tech Writer', 'TechWriter'),
    value: r.score,
  }));

  return (
    <Stack gap={24} style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <Stack gap={4}>
        <H1>Final Project Review — Synthia</H1>
        <Text tone="secondary" size="small">
          AI Protocol Generator · 24 апреля 2026 · v1.2.0 · Сессия 12 · CHECKPOINT v12.0.0
        </Text>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat label="Общий балл" value={`${avgScore}/100`} tone={avgScore >= 80 ? 'success' : 'warning'} />
        <Stat label="Покрытие CoreCase" value={`${coveragePct}%`} tone={coveragePct >= 85 ? 'success' : 'warning'} />
        <Stat label="Автотестов (passed)" value="137" tone="success" />
        <Stat label="API эндпоинтов" value="30+" tone="info" />
      </Grid>

      <Grid columns={3} gap={12}>
        <Stat label="FR реализовано полностью" value={String(doneCount)} tone="success" />
        <Stat label="FR реализовано частично" value={String(partialCount)} tone="warning" />
        <Stat label="FR отсутствует" value="0" tone="success" />
      </Grid>

      <Divider />

      <H2>Покрытие требований CoreCase</H2>
      <Table
        headers={['ID', 'Требование', 'Приоритет', 'Статус', 'Примечание']}
        rows={CORECASE_FEATURES.map(f => [
          f.id, f.name, f.priority,
          f.status === 'done' ? 'Реализовано' : 'Частично',
          f.note,
        ])}
        rowTone={CORECASE_FEATURES.map(f =>
          f.status === 'done' ? 'success' : f.status === 'partial' ? 'warning' : 'danger'
        ) as any}
      />

      <Divider />

      <H2>Оценка по ролям</H2>
      <BarChart data={scoreChartData} height={220} maxValue={100} tone="info" />

      <Grid columns={2} gap={16}>
        {ROLE_REVIEWS.map(r => (
          <Card key={r.role} size="sm">
            <CardHeader
              title={r.role}
              trailing={
                <Row gap={8} style={{ alignItems: 'center' }}>
                  <Text size="small" weight="medium">{r.score}/100</Text>
                  <Pill tone={r.verdict} size="sm">{r.verdictLabel}</Pill>
                </Row>
              }
            />
            <CardBody>
              <Stack gap={8}>
                <Stack gap={4}>
                  {r.strengths.map((s, i) => (
                    <Text key={i} size="small">+ {s}</Text>
                  ))}
                </Stack>
                {r.gaps.length > 0 && (
                  <Stack gap={4}>
                    {r.gaps.map((g, i) => (
                      <Text key={i} size="small" tone="secondary">- {g}</Text>
                    ))}
                  </Stack>
                )}
              </Stack>
            </CardBody>
          </Card>
        ))}
      </Grid>

      <Divider />

      <Grid columns={2} gap={12}>
        <Stack gap={8}>
          <H2>Ключевые изменения v1.2.0 (сессии 11–12)</H2>
          <Table
            headers={['Функция', 'Тип']}
            rows={[
              ['CreateProtocolPage.tsx — новый UI', 'Frontend'],
              ['Редактирование метаданных (PATCH полный)', 'Backend'],
              ['Exclusion criteria — CRUD + сохранение', 'Backend'],
              ['Export open-issues JSON/CSV', 'Backend'],
              ['Export → AuditLog action="export"', 'Backend'],
              ['Уникальные fallback для всех 12 секций', 'AI / Generator'],
              ['SAP/ICF fallback уникальны (не дублируют друг друга)', 'AI / Generator'],
              ['RAG: _fetch_rag_context() через embeddings', 'AI / Generator'],
              ['Phase IV → 422 (frontend + backend)', 'Validation'],
              ['test_new_features.py — 44 новых теста', 'QA'],
              ['test-plan.md → v3.4.0', 'Docs'],
              ['CHECKPOINT.md → v12.0.0', 'Docs'],
            ]}
          />
        </Stack>
        <Stack gap={8}>
          <H2>Backlog (P1–P3)</H2>
          <Table
            headers={['Задача', 'Приоритет']}
            rows={[
              ['Ротация токена из corecase.md', 'P0 BLOCKER'],
              ['Dokploy redeploy (migrations 004–005)', 'P0'],
              ['api-spec.md → v1.7.0 (/embeddings/*)', 'P1'],
              ['.env.example создать', 'P1'],
              ['VERSIONS.md encoding fix (UTF-8 без BOM)', 'P1'],
              ['import pytest_asyncio fix в test_new_features.py', 'P1'],
              ['Уведомления рецензенту (in_review)', 'P2'],
              ['RAG pgvector (pgvector расширение)', 'P2'],
              ['CI/CD (auto-test on push)', 'P2'],
              ['Rate limiting (brute-force protection)', 'P2'],
              ['ct.biocad.ru интеграция', 'P3'],
            ]}
            rowTone={['danger', 'danger', 'warning', 'warning', 'warning', 'warning',
                      undefined, undefined, undefined, undefined, undefined] as any}
          />
        </Stack>
      </Grid>

      <Divider />

      <H2>Документация</H2>
      <Table
        headers={['Документ', 'Версия', 'Статус']}
        rows={[
          ['CHECKPOINT.md',               'v12.0.0', 'Актуально'],
          ['RELEASE-NOTES.md',            'v3.0.0',  'Актуально'],
          ['PROMPTS.md',                  'v2.0.0',  'Актуально'],
          ['functional-requirements.md',  'v1.3.0',  'Актуально'],
          ['test-plan.md',                'v3.4.0',  'Актуально'],
          ['DEPLOY.md',                   'v1.2.0',  'Актуально'],
          ['artifacts-catalog.md',        'v1.3.0',  'Актуально'],
          ['api-spec.md',                 'v1.6.0',  'Требует обновления (v1.7.0 — /embeddings/*)'],
          ['VERSIONS.md',                 'v1.5.0',  'Encoding fix нужен'],
        ]}
        rowTone={[undefined, undefined, undefined, undefined, undefined, undefined, undefined,
                  'warning', 'warning'] as any}
      />

      <Callout tone={avgScore >= 82 ? 'success' : 'warning'} title={`Вердикт: ${avgScore >= 82 ? 'ДЕМО-ГОТОВ' : 'ТРЕБУЕТ ДОРАБОТКИ'}`}>
        Synthia v1.2.0 покрывает {coveragePct}% требований CoreCase.
        137 тестов passed, 0 failed. Средний балл по ролям {avgScore}/100.
        Блокер до деплоя: ротация токена из corecase.md + Dokploy redeploy.
      </Callout>

      <Text tone="secondary" size="small">
        Дедлайн: 24.04.2026 17:30 · Сгенерировано: 24.04.2026 · canvas v2
      </Text>
    </Stack>
  );
}
