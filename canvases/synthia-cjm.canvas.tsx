import {
  Stack, Grid, H1, H2, H3, Text, Divider, Row, Card, CardHeader, CardBody,
  Pill, Stat, Table, Callout, Select, useCanvasState,
} from 'cursor/canvas';

type CjmKey = 'create' | 'generate' | 'search' | 'archive';

interface Stage {
  num: number;
  title: string;
  action: string;
  thought: string;
  emotion: string;
  tone: 'neutral' | 'positive' | 'warning';
}

interface CjmData {
  title: string;
  persona: string;
  role: string;
  goal: string;
  pain: string;
  success: string;
  stages: Stage[];
  painPoints: string[];
  opportunities: string[];
  metrics: string[];
  emotionCurve: number[];
}

const CJMS: Record<CjmKey, CjmData> = {
  create: {
    title: 'Создание протокола',
    persona: 'Андрей Клинический',
    role: 'Clinical Researcher',
    goal: 'Завести новый протокол КИ без ошибок менее чем за 5 минут',
    pain: 'Копирует старые протоколы вручную — "хвосты" от прошлых версий',
    success: 'Протокол создан, все обязательные поля заполнены, готов к AI-генерации',
    stages: [
      { num: 1, title: 'Вход в систему', action: 'Открывает Synthia, видит список протоколов', thought: '"Надо создать протокол для Phase III RCT"', emotion: 'Нейтрально', tone: 'neutral' },
      { num: 2, title: 'Создание', action: 'Жмёт [+ Новый протокол], заполняет обязательные поля', thought: '"Форма понятная, поля с примерами — удобно"', emotion: 'Сосредоточен', tone: 'neutral' },
      { num: 3, title: 'Теги', action: 'Добавляет теги через Enter: oncology, phase-III, biocad', thought: '"Цветные чипы — сразу понятно какой тег"', emotion: 'Доволен', tone: 'positive' },
      { num: 4, title: 'Сохранение', action: 'Нажимает [Создать протокол], видит карточку протокола', thought: '"Готово! Теперь надо запустить AI-генерацию"', emotion: 'Удовлетворён', tone: 'positive' },
    ],
    painPoints: [
      'Нет подсказок для сложных полей (population, dosing)',
      'Нет шаблонов per therapeutic area',
      'Нет валидации минимального набора критериев включения',
    ],
    opportunities: [
      'Smart defaults по therapeutic_area + phase',
      'AI-подсказки для inclusion_criteria',
      'Импорт из DOCX/PDF предыдущего протокола',
    ],
    metrics: [
      'Время создания: < 5 мин (цель)',
      '% заполненных optional полей: > 70%',
      'Ошибок валидации при создании: 0',
    ],
    emotionCurve: [50, 55, 70, 75],
  },
  generate: {
    title: 'AI Генерация',
    persona: 'Светлана Медрайтер',
    role: 'Medical Writer',
    goal: 'Получить GCP-корректный черновик протокола за один клик',
    pain: 'Создаёт разделы вручную — 2–3 дня работы на один протокол',
    success: 'AI создал все 9 разделов, GCP score > 75%, черновик готов к ревью',
    stages: [
      { num: 1, title: 'Запуск', action: 'Добавляет комментарий к версии, жмёт [Генерировать]', thought: '"Буду делать другие задачи пока идёт генерация"', emotion: 'Спокойно', tone: 'neutral' },
      { num: 2, title: 'SynthiaOrb', action: 'Видит анимированный орб, счётчик секций 3/9, 5/9...', thought: '"Визуально понятно что происходит!"', emotion: 'Интерес', tone: 'positive' },
      { num: 3, title: 'Черновик', action: 'Нажимает [Черновик] — модал со всеми разделами', thought: '"Objectives — отлично. Статистика — надо уточнить"', emotion: 'Аналитически', tone: 'neutral' },
      { num: 4, title: 'Секция-перегенерация', action: 'Жмёт [Перегенерировать] для раздела Statistics', thought: '"Удобно — не надо перегенерировать весь протокол"', emotion: 'Доволен', tone: 'positive' },
      { num: 5, title: 'GCP проверка', action: 'Жмёт [GCP-проверка], видит score ICH 82% / РФ 78%', thought: '"2 замечания medium — понятные recommendations"', emotion: 'Уверен', tone: 'positive' },
    ],
    painPoints: [
      'Нет индикатора прогресса с названием текущей секции',
      'Нет inline-редактирования текста секции в черновике',
      'Нет сравнения версий (diff) между v1 и v2',
    ],
    opportunities: [
      'Live streaming секций по мере генерации',
      'Inline edit разделов прямо в DraftModal',
      'Diff view: что изменилось между версиями',
    ],
    metrics: [
      'Время генерации 9 секций: < 90 сек',
      'GCP ICH score: > 75% (цель)',
      'Ручных правок после AI: < 20% контента',
    ],
    emotionCurve: [60, 70, 65, 80, 85],
  },
  search: {
    title: 'Поиск и просмотр',
    persona: 'Марина Аудитор',
    role: 'Regulatory Auditor',
    goal: 'Найти актуальную версию протокола и скачать Audit Trail за < 30 секунд',
    pain: 'В папках на сервере — 12 файлов "protocol_final_v3_FINAL_rev2.docx"',
    success: 'Нашла нужный протокол, видит статус Active, скачала Audit Trail PDF',
    stages: [
      { num: 1, title: 'Поиск', action: 'Вводит "oncology phase III" в строку поиска', thought: '"Сразу выдало 3 результата с autocomplete!"', emotion: 'Удивлена (приятно)', tone: 'positive' },
      { num: 2, title: 'Фильтры', action: 'Применяет фильтр: Статус = Generated, Фаза = III', thought: '"Активные фильтры считаются — знаю что включены"', emotion: 'Доволен', tone: 'positive' },
      { num: 3, title: 'Статус блокировки', action: 'Видит badge [Заблокирован] рядом с названием', thought: '"Данные исследования зафиксированы — это надёжно"', emotion: 'Уверен', tone: 'positive' },
      { num: 4, title: 'Аудит Trail', action: 'Переходит во вкладку Аудит, видит все события', thought: '"Вижу кто и когда делал AI генерацию — полный trail"', emotion: 'Удовлетворён', tone: 'positive' },
      { num: 5, title: 'Экспорт', action: 'Жмёт [DOCX] и [Печать/PDF] в аудите', thought: '"Профессиональный документ, watermark — всё есть"', emotion: 'Доволен', tone: 'positive' },
    ],
    painPoints: [
      'Нет global search по содержимому секций',
      'Нет bulk export нескольких протоколов',
      'Нет статуса "Approved by QA" в workflow',
    ],
    opportunities: [
      'Семантический поиск по тексту секций (RAG)',
      'Quick preview карточки при hover в списке',
      'Статус workflow: Draft → Generated → QA Review → Approved',
    ],
    metrics: [
      'Время поиска нужного протокола: < 30 сек',
      'Время выгрузки Audit Trail PDF: < 5 сек',
      'Ложных срабатываний в поиске: < 10%',
    ],
    emotionCurve: [55, 70, 75, 80, 85],
  },
  archive: {
    title: 'Версионирование и архив',
    persona: 'Игорь Менеджер КИ',
    role: 'Study Manager',
    goal: 'Обновить протокол по ревью, сохранив историю всех версий',
    pain: 'Неясно какая версия актуальная; правки теряются; нет changelog',
    success: 'Новая версия создана, старая заархивирована автоматически, diff покажет изменения, audit trail полный',
    stages: [
      { num: 1, title: 'Ревью замечаний', action: 'Читает GCP-замечания из предыдущей проверки', thought: '"2 замечания high — надо перегенерировать"', emotion: 'Сосредоточен', tone: 'neutral' },
      { num: 2, title: 'Комментарий', action: 'Вводит: "Уточнены критерии включения по ревью QA #204"', thought: '"Хорошо что есть поле для обоснования изменения"', emotion: 'Деловито', tone: 'neutral' },
      { num: 3, title: 'Перегенерация', action: 'Жмёт [Перегенерировать], видит предупреждение об архивировании', thought: '"Понятно — старая версия уйдёт в Archive автоматически"', emotion: 'Уверен', tone: 'positive' },
      { num: 4, title: 'Diff v1 → v2', action: 'Открывает Diff-панель: видит добавленное / удалённое по секциям', thought: '"Вижу точно что изменилось — можно показать рецензенту"', emotion: 'Очень доволен', tone: 'positive' },
      { num: 5, title: 'GCP повторно', action: 'Запускает GCP check, score вырос до 88%, нажимает «Одобрить»', thought: '"Замечания устранены. 4-eyes approve — другой коллега подтвердит"', emotion: 'Удовлетворён', tone: 'positive' },
    ],
    painPoints: [
      'Нет уведомления команды о новой версии (email/Slack) — P2 backlog',
      'Нет аннотации к архивной версии причины замены',
      'После approve протокол заблокирован — нельзя редактировать без copy',
    ],
    opportunities: [
      'Webhook/email нотификация о новой версии (P2)',
      'Changelog с комментариями всех версий (P2)',
      'Smart copy: форк заблокированного протокола одним кликом (реализовано)',
    ],
    metrics: [
      'Версии видны без потери истории: 100%',
      'Время обнаружения нужной версии: < 10 сек',
      'Audit trail: каждая версия залогирована',
    ],
    emotionCurve: [55, 60, 70, 80, 88],
  },
};

const CJM_OPTIONS = [
  { value: 'create', label: 'CJM 1: Создание протокола' },
  { value: 'generate', label: 'CJM 2: AI Генерация' },
  { value: 'search', label: 'CJM 3: Поиск и просмотр' },
  { value: 'archive', label: 'CJM 4: Версионирование' },
];

function emotionBar(value: number): string {
  const filled = Math.round(value / 10);
  const empty = 10 - filled;
  return `${'█'.repeat(filled)}${'░'.repeat(empty)} ${value}%`;
}

export default function SynthiaCJM() {
  const [selected, setSelected] = useCanvasState<CjmKey>('cjm', 'create');
  const data = CJMS[selected];

  const emotionRows = data.stages.map((s, i) => [
    `${s.num}. ${s.title}`,
    s.emotion,
    emotionBar(data.emotionCurve[i] ?? 50),
  ]);

  return (
    <Stack gap={24}>
      <Row gap={16} align="end">
        <Stack gap={4} style={{ flex: 1 }}>
          <H1>Synthia — Customer Journey Maps</H1>
          <Text tone="secondary" size="small">
            Пути пользователей в AI-генераторе протоколов КИ · 4 ключевых сценария
          </Text>
        </Stack>
        <Select
          value={selected}
          options={CJM_OPTIONS}
          onChange={v => setSelected(v as CjmKey)}
        />
      </Row>

      <Divider />

      {/* Persona */}
      <Card>
        <CardHeader trailing={<Pill size="sm">{data.role}</Pill>}>{data.persona}</CardHeader>
        <CardBody>
          <Grid columns={3} gap={16}>
            <Stack gap={4}>
              <Text size="small" weight="medium">Цель</Text>
              <Text size="small" tone="secondary">{data.goal}</Text>
            </Stack>
            <Stack gap={4}>
              <Text size="small" weight="medium">Боль</Text>
              <Text size="small" tone="secondary">{data.pain}</Text>
            </Stack>
            <Stack gap={4}>
              <Text size="small" weight="medium">Критерий успеха</Text>
              <Text size="small" tone="secondary">{data.success}</Text>
            </Stack>
          </Grid>
        </CardBody>
      </Card>

      {/* Journey stages */}
      <Stack gap={8}>
        <H2>Путь пользователя</H2>
        <Grid columns={data.stages.length > 4 ? 5 : data.stages.length} gap={12}>
          {data.stages.map(s => (
            <Card key={s.num} size="small">
              <CardHeader
                trailing={
                  <Pill size="sm" tone={s.tone === 'positive' ? 'success' : s.tone === 'warning' ? 'warning' : 'neutral'}>
                    {s.emotion}
                  </Pill>
                }
              >
                {s.num}. {s.title}
              </CardHeader>
              <CardBody>
                <Stack gap={8}>
                  <Stack gap={2}>
                    <Text size="small" weight="medium">Действие</Text>
                    <Text size="small" tone="secondary">{s.action}</Text>
                  </Stack>
                  <Stack gap={2}>
                    <Text size="small" weight="medium">Мысли</Text>
                    <Text size="small" tone="secondary">{s.thought}</Text>
                  </Stack>
                </Stack>
              </CardBody>
            </Card>
          ))}
        </Grid>
      </Stack>

      {/* Emotion curve */}
      <Stack gap={8}>
        <H2>Эмоциональная кривая</H2>
        <Table
          headers={['Этап', 'Эмоция пользователя', 'Уровень вовлечённости']}
          rows={emotionRows}
        />
      </Stack>

      <Divider />

      {/* Insights */}
      <Grid columns={3} gap={16}>
        <Stack gap={8}>
          <H3>Pain Points</H3>
          {data.painPoints.map((p, i) => (
            <Callout key={i} tone="warning">{p}</Callout>
          ))}
        </Stack>
        <Stack gap={8}>
          <H3>Opportunities</H3>
          {data.opportunities.map((o, i) => (
            <Callout key={i} tone="info">{o}</Callout>
          ))}
        </Stack>
        <Stack gap={8}>
          <H3>Success Metrics</H3>
          {data.metrics.map((m, i) => (
            <Callout key={i} tone="success">{m}</Callout>
          ))}
        </Stack>
      </Grid>

      <Divider />

      {/* UX Improvements backlog */}
      <Stack gap={12}>
        <H2>UX Улучшения — Приоритетный план</H2>
        <Table
          headers={['Приоритет', 'Улучшение', 'Сценарий', 'Ожидаемый эффект']}
          rows={[
            ['P1', 'Live streaming секций при генерации', 'CJM 2', 'Снижение тревожности; ощущение прогресса'],
            ['DONE', 'Diff view v1 vs v2 с highlight изменений', 'CJM 4', 'Реализовано: unified diff по секциям + слайд-панель'],
            ['P1', 'Quick preview карточки при hover в списке', 'CJM 3', 'Меньше переходов; MTLV < 15 сек'],
            ['P1', 'Smart defaults: therapeutic_area → шаблон полей', 'CJM 1', 'Сокращение времени создания на 40%'],
            ['P1', 'Inline edit разделов прямо в DraftModal', 'CJM 2', 'Меньше итераций перегенерации'],
            ['P2', 'Статус workflow: Generated → QA Review → Approved', 'CJM 3', 'Полный lifecycle протокола в системе'],
            ['P2', 'Webhook/email нотификация о новой версии', 'CJM 4', 'Команда не пропускает обновления'],
            ['P2', 'Семантический поиск по тексту секций (RAG)', 'CJM 3', 'Находит нужный контент, а не только metadata'],
            ['P3', 'Bulk export нескольких протоколов', 'CJM 3', 'Аудиторские проверки: меньше ручных операций'],
            ['P3', 'Import из DOCX/PDF для создания протокола', 'CJM 1', 'Перенос legacy протоколов в систему'],
          ]}
          rowTone={[
            'warning', 'warning',
            undefined, undefined, undefined,
            undefined, undefined, undefined,
            undefined, undefined,
          ]}
        />
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value="4" label="Ключевых сценария CJM" />
        <Stat value="DONE" label="Diff view реализован" tone="success" />
        <Stat value="88%" label="Макс. GCP score (CJM 4)" tone="success" />
        <Stat value="< 30s" label="Цель: поиск протокола" tone="success" />
      </Grid>

      <Text tone="secondary" size="small">
        Synthia CJM v1.0 · 24.04.2026 · На основе требований ICH E6(R2) GCP
      </Text>
    </Stack>
  );
}
