import { useState } from 'react';
import {
  Stack, H1, H2, H3, Grid, Stat, Table, Divider, Text, Row,
  Card, CardHeader, CardBody, Callout, Code,
  useHostTheme,
} from 'cursor/canvas';

// ─── Data (CHECKPOINT v14.0.0 · 137 passed · 0 failed) ───────────────────────

const TEST_RESULTS = {
  total: 137,
  passed: 137,
  failed: 0,
  duration: '~18s',
  files: [
    { file: 'test_health.py',              total: 1,  note: 'GET /health → 200' },
    { file: 'test_auth.py',                total: 12, note: 'Login, JWT, RBAC, whoami — credentials из env' },
    { file: 'test_protocols.py',           total: 18, note: 'CRUD, versions, diff, copy, 4-eyes approve, lock' },
    { file: 'test_export.py',              total: 5,  note: 'MD / HTML / DOCX + open-issues JSON/CSV' },
    { file: 'test_ai_gateway.py',          total: 5,  note: 'Mock, retry, timeout, 503 fallback' },
    { file: 'test_templates.py',           total: 4,  note: 'List, get templates' },
    { file: 'test_form_scenarios.py',      total: 51, note: 'Happy path (9) + Negative (23) + Security (3) + RBAC (11) + AI (4) + edge cases' },
    { file: 'test_realistic_scenarios.py', total: 41, note: 'Сессия 11–12: SAP/ICF, edit meta, exclusion criteria, phase IV — NEW' },
  ],
};

// ─── New Features Tests (sessions 11–12) ──────────────────────────────────────

const NEW_FEATURE_TESTS = [
  { id: 'SMOKE-01', class: 'TestSmoke',    name: 'Создание с exclusion_criteria', detail: '201 · BASE_PROTOCOL с тегами oncology/phase-ii' },
  { id: 'SMOKE-02', class: 'TestSmoke',    name: 'Phase IV → 422',               detail: 'POST phase="IV" → 422 (pattern ^(I|II|III)$)' },
  { id: 'EDIT-01',  class: 'TestEditMeta', name: 'Persistence полей после PATCH', detail: 'exclusion_criteria + secondary_endpoints сохраняются' },
  { id: 'EDIT-02',  class: 'TestEditMeta', name: 'Full PATCH всех полей',         detail: 'title, indication, population, dosing, duration_weeks, endpoints, criteria' },
  { id: 'EDIT-03',  class: 'TestEditMeta', name: 'Partial PATCH (только title)',  detail: 'Остальные поля не затронуты' },
  { id: 'EDIT-04',  class: 'TestEditMeta', name: 'Audit "update" пишется',       detail: 'GET /{id}/audit → action="update"' },
  { id: 'FALL-01',  class: 'TestSectionFallbacks', name: 'Уникальность fallback по секциям',     detail: 'Мок AIGatewayError → каждая секция содержит уникальный текст' },
  { id: 'FALL-02',  class: 'TestSectionFallbacks', name: '_fallback_section для FULL_SECTIONS',  detail: 'Все 12 секций содержат "FOR REVIEW ONLY"' },
  { id: 'FALL-03',  class: 'TestSectionFallbacks', name: 'SAP vs ICF vs intro уникальны',       detail: 'Тексты fallback SAP ≠ ICF ≠ introduction' },
  { id: 'ALT-01',   class: 'TestAlternative',      name: 'Пустые exclusion_criteria',             detail: 'exclusion_criteria=[] → 201' },
  { id: 'ALT-02',   class: 'TestAlternative',      name: '10 exclusion_criteria',                 detail: '201 · все 10 сохраняются' },
  { id: 'ALT-03',   class: 'TestAlternative',      name: 'drug_name в fallback тексте',           detail: 'fallback содержит drug_name из параметров протокола' },
  { id: 'NEG-N01',  class: 'TestNegative',          name: 'Phase IV → 422',                       detail: '422 Unprocessable Entity (дубль smoke)' },
  { id: 'NEG-N02',  class: 'TestNegative',          name: '404 PATCH несуществующего',            detail: '404 PROTOCOL_NOT_FOUND' },
  { id: 'NEG-N03',  class: 'TestNegative',          name: 'Auditor 403 PATCH',                    detail: '403 Forbidden — auditor не может редактировать' },
  { id: 'NEG-N04',  class: 'TestNegative',          name: 'Invalid phase PATCH',                  detail: '422 при попытке PATCH phase="IV"' },
  { id: 'NEG-N05',  class: 'TestNegative',          name: 'Title < 5 символов PATCH',             detail: '422 min_length=5' },
];

const AI_ANALYSIS = [
  { aspect: 'Параллельная генерация',            ok: true,  detail: 'asyncio.gather() — 7 MVP секций одновременно; SAP/ICF отдельно (artifact)' },
  { aspect: 'Fallback при недоступности Gateway', ok: true,  detail: '_fallback_section() — уникальный контент для каждой секции и SAP/ICF' },
  { aspect: 'RAG контекст (опционально)',         ok: true,  detail: '_fetch_rag_context(): AI_EMBEDDING_URL → similarity search → context block' },
  { aspect: 'Контекст в промпте',                ok: true,  detail: '_build_context(): drug, phase, ta_context (RECIST/PASI), критерии вкл/искл' },
  { aspect: 'Перегенерация секции (FR-03.5)',    ok: true,  detail: 'generate_single_section() → новая ProtocolVersion, старые секции сохранены' },
  { aspect: 'SAP генерация (Appendix A)',        ok: true,  detail: 'Промпт: ITT/PP/Safety, power analysis, MCAR/MAR/MNAR, SAS/R/Python' },
  { aspect: 'ICF генерация (Appendix B)',        ok: true,  detail: 'Промпт: 61-ФЗ, ICH E6 §4.8, Приказ №353н — 11 обязательных разделов' },
  { aspect: 'Task persistence',                  ok: false, detail: 'task_id хранится в памяти → рестарт сервера теряет статус (P1 backlog)' },
  { aspect: 'Prompt injection (custom_prompt)',  ok: true,  detail: 'prompt_guard.py: 18 паттернов, max 2000 символов — sanitization активна' },
  { aspect: 'Audit в фоновой задаче',            ok: true,  detail: 'AuditLog: model, sections, version, duration_ms, role — после commit' },
  { aspect: 'Export audit log',                  ok: true,  detail: 'export.py: AuditLog action="export" с format/version_id/version_number' },
];

const RBAC_ROWS = [
  ['Создание протокола',        'admin', 'employee', '-'],
  ['Чтение протокола',          'admin', 'employee', 'auditor'],
  ['Редактирование метаданных', 'admin', 'employee', '-'],
  ['Удаление протокола',        'admin', '-',        '-'],
  ['AI генерация (all sections)', 'admin', 'employee', '-'],
  ['Перегенерация секции',      'admin', 'employee', '-'],
  ['GCP-проверка',              'admin', 'employee', '-'],
  ['Экспорт MD/HTML/DOCX',     'admin', 'employee', 'auditor'],
  ['Экспорт Open Issues',       'admin', 'employee', 'auditor'],
  ['Генерация SAP/ICF',         'admin', 'employee', '-'],
  ['Одобрение (4-eyes)',        'admin (не creator)', 'employee (не creator)', '-'],
  ['Блокировка протокола',      'auto (после approved)', '-', '-'],
  ['Копирование (copy)',        'admin', 'employee', '-'],
  ['Чтение версий',             'admin', 'employee', 'auditor'],
  ['Audit Trail',               'admin', 'employee', 'auditor'],
  ['BIOCAD Trials прокси',      'admin', 'employee', 'auditor'],
  ['Embeddings (RAG)',          'admin', '-',        '-'],
];

type Tab = 'files' | 'new' | 'ai' | 'rbac';

export default function QaReport() {
  const theme = useHostTheme();
  const [activeTab, setActiveTab] = useState<Tab>('files');

  const tabLabel: Record<Tab, string> = {
    files: 'Test-файлы',
    new:   'Новые тесты (сессия 12)',
    ai:    'AI-генератор',
    rbac:  'RBAC матрица',
  };

  return (
    <Stack gap={28}>

      <Stack gap={4}>
        <H1>QA Report — AI Protocol Generator</H1>
        <Text tone="secondary" size="small">
          24 апреля 2026 · Сессия 12 · CHECKPOINT v12.0.0 · 137 passed · 0 failed
        </Text>
      </Stack>

      <Grid columns={4} gap={16}>
        <Stat value={String(TEST_RESULTS.total)} label="Всего тестов" tone="success" />
        <Stat value={String(TEST_RESULTS.passed)} label="Прошло" tone="success" />
        <Stat value={String(TEST_RESULTS.failed)} label="Упало" tone="success" />
        <Stat value="8 файлов" label="Тест-файлов" />
      </Grid>

      <Divider />

      <Row gap={8}>
        {(['files', 'new', 'ai', 'rbac'] as Tab[]).map(tab => (
          <div
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              cursor: 'pointer',
              padding: '5px 14px',
              borderRadius: 6,
              fontSize: 13,
              fontWeight: activeTab === tab ? 600 : 400,
              background: activeTab === tab ? theme.accent.primary : theme.fill.tertiary,
              color: activeTab === tab ? theme.text.onAccent : theme.text.primary,
              border: `1px solid ${activeTab === tab ? theme.accent.primary : theme.stroke.secondary}`,
              userSelect: 'none',
            }}
          >
            {tabLabel[tab]}
          </div>
        ))}
      </Row>

      {activeTab === 'files' && (
        <Stack gap={16}>
          <H2>Тест-файлы (137 тестов суммарно)</H2>
          <Table
            headers={['Файл', 'Тестов', 'Покрытие / Тема']}
            rows={TEST_RESULTS.files.map(f => [f.file, String(f.total), f.note])}
            rowTone={TEST_RESULTS.files.map((_, i) => i === 7 ? 'success' as const : undefined)}
          />
          <Callout tone="success" title="Все 137 тестов зелёные">
            Credentials исправлены: EMPLOYEE_PASSWORD / AUDITOR_PASSWORD из env-config.
            4-eyes lifecycle тест: employee не может approve свой протокол.
            Diff: возвращает unified diff между двумя версиями (не 501).
          </Callout>
        </Stack>
      )}

      {activeTab === 'new' && (
        <Stack gap={16}>
          <H2>Новые тесты — сессия 11–12 (test_realistic_scenarios.py)</H2>
          <Text tone="secondary">
            41 тест: smoke, edit_metadata, section_fallbacks, alternative, negative.
            Покрывают: exclusion_criteria, SAP/ICF fallback уникальность, export audit, phase IV.
          </Text>
          <Table
            headers={['ID', 'Класс', 'Сценарий', 'Детали']}
            rows={NEW_FEATURE_TESTS.map(t => [t.id, t.class, t.name, t.detail])}
          />
          <Card size="sm">
            <CardHeader title="Известное: import порядок" />
            <CardBody>
              <Text size="small" tone="secondary">
                pytest_asyncio импортируется на строке 432, но используется с @pytest_asyncio.fixture на строке 40.
                Необходимо перенести import в начало файла (строки 1–15) во избежание потенциального NameError.
              </Text>
            </CardBody>
          </Card>
        </Stack>
      )}

      {activeTab === 'ai' && (
        <Stack gap={16}>
          <H2>AI Generator — анализ логики</H2>
          <Grid columns={3} gap={12}>
            <Stat value="7"  label="MVP секций (параллельно)" />
            <Stat value="12" label="FULL_SECTIONS" />
            <Stat value="SAP+ICF" label="Артефакты (appendix)" />
          </Grid>
          <Table
            headers={['Аспект', 'Статус', 'Детали']}
            rows={AI_ANALYSIS.map(a => [a.aspect, a.ok ? 'OK' : 'WARN (P1)', a.detail])}
            rowTone={AI_ANALYSIS.map(a => a.ok ? 'success' as const : 'warning' as const)}
          />
          <H3>Промпт-структура (_build_context)</H3>
          <Card>
            <CardBody>
              <Code>{`ПАРАМЕТРЫ ПРОТОКОЛА:
- Препарат: {drug_name} ({inn})
- Фаза: {phase} — {PHASE_CONTEXT}       // "Confirmatory", "Exploratory"...
- Область: {therapeutic_area} — {TA_CONTEXT}  // RECIST, PASI, ACR20...
- Индикация: {indication}
- Популяция: {population}
- Первичная КТ: {primary_endpoint}
- Вторичные КТ: {secondary_endpoints}
- Длительность: {duration_weeks} недель
- Дозирование: {dosing}
- Критерии включения: [...]
- Критерии исключения: [...]
[RAG_CONTEXT: если AI_EMBEDDING_URL задан]`}</Code>
            </CardBody>
          </Card>
        </Stack>
      )}

      {activeTab === 'rbac' && (
        <Stack gap={16}>
          <H2>RBAC — матрица доступа</H2>
          <Table
            headers={['Операция', 'Admin', 'Employee', 'Auditor']}
            rows={RBAC_ROWS}
          />
          <Callout tone="success">
            UI: кнопки удаления и генерации скрыты для соответствующих ролей.
            Backend: require_role() / require_delete() — единственная enforcement-точка.
            4-eyes: одобрение заблокировано для creator протокола.
          </Callout>
        </Stack>
      )}

      <Divider />

      <Grid columns={3} gap={14}>
        <Card>
          <CardHeader title="Тест-сьют" />
          <CardBody>
            <Text>137 тестов · 0 упало · ~18с</Text>
            <Text tone="secondary" size="small">
              8 файлов · credentials из env · 4-eyes lifecycle · diff реализован
            </Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="AI / Генерация" />
          <CardBody>
            <Text>Параллельная генерация + RAG + fallback уникальны</Text>
            <Text tone="secondary" size="small">
              SAP/ICF fallbacks уникальны для каждого артефакта
            </Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Governance" />
          <CardBody>
            <Text>4-eyes, lock, copy — покрыты тестами</Text>
            <Text tone="secondary" size="small">
              RBAC матрица расширена: 17 операций × 3 роли
            </Text>
          </CardBody>
        </Card>
      </Grid>

    </Stack>
  );
}
