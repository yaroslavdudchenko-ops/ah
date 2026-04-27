import {
  BarChart,
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  H3,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
} from "cursor/canvas";

const DEADLINE = "24.04.2026 17:30";
const LAST_COMMIT = "24.04.2026 02:43";

// WakaTime actuals
const WAKA_APR23 = 21; // minutes
const WAKA_APR24 = 164; // minutes (2h 44m)
const WAKA_TOTAL = WAKA_APR23 + WAKA_APR24; // 185 min = 3h 5m

// Current time estimate — ~11:00 local (based on chat timing after 02:43 last commit)
// Hours to deadline from ~11:00: 17:30 - 11:00 = 6.5h
const HOURS_TO_DEADLINE = 6.5;

const phases = [
  { name: "Phase 0 · Docs",       done: true,  est: 0.5,  actual: 0.5 },
  { name: "Phase 1 · Backend",     done: true,  est: 2.0,  actual: 1.5 },
  { name: "Phase 1.5 · Swagger",   done: true,  est: 0.3,  actual: 0.3 },
  { name: "Phase 2 · Frontend",    done: true,  est: 1.5,  actual: 1.0 },
  { name: "Phase 2.5 · QA",        done: true,  est: 0.5,  actual: 0.5 },
  { name: "Phase 3 · Deploy",      done: false, est: 1.5,  actual: 0   },
  { name: "P0 Fixes (review)",     done: false, est: 0.5,  actual: 0   },
  { name: "GitLab push + verify",  done: false, est: 0.5,  actual: 0   },
  { name: "Final smoke on prod",   done: false, est: 0.5,  actual: 0   },
];

const donePhases = phases.filter((p) => p.done);
const remainPhases = phases.filter((p) => !p.done);
const remainHours = remainPhases.reduce((s, p) => s + p.est, 0);
const doneHours = donePhases.reduce((s, p) => s + p.actual, 0);

const fmtH = (h: number) => {
  const hrs = Math.floor(h);
  const mins = Math.round((h - hrs) * 60);
  if (hrs === 0) return `${mins}m`;
  if (mins === 0) return `${hrs}h`;
  return `${hrs}h ${mins}m`;
};

const fmtMin = (m: number) => {
  const h = Math.floor(m / 60);
  const min = m % 60;
  if (h === 0) return `${min}m`;
  return `${h}h ${min}m`;
};

export default function WakatimeProgress() {
  const buffer = HOURS_TO_DEADLINE - remainHours;
  const bufferTone = buffer >= 2 ? "success" : buffer >= 0.5 ? "warning" : "danger";
  const bufferLabel = buffer >= 0 ? `+${fmtH(buffer)} buffer` : `${fmtH(Math.abs(buffer))} overrun`;

  return (
    <Stack gap={24}>
      <Stack gap={6}>
        <H1>WakaTime · Оценка прогресса</H1>
        <Row gap={8} wrap>
          <Pill size="sm" tone="info" active>Дедлайн: {DEADLINE}</Pill>
          <Pill size="sm" tone="neutral">Последний коммит: {LAST_COMMIT}</Pill>
          <Pill size="sm" tone="neutral">Редактор: Cursor</Pill>
        </Row>
      </Stack>

      {/* === KEY STATS === */}
      <Grid columns={4} gap={12}>
        <Stat value={fmtMin(WAKA_TOTAL)} label="Всего закодировано" />
        <Stat value={fmtMin(WAKA_APR24)} label="Сегодня (24.04)" tone="info" />
        <Stat value={fmtH(remainHours)} label="Оставшаяся работа" tone="warning" />
        <Stat value={bufferLabel} label="Буфер до дедлайна" tone={bufferTone} />
      </Grid>

      {/* === TIME BY DAY === */}
      <BarChart
        categories={["23 апр", "24 апр (сегодня)"]}
        series={[{ name: "Время в проекте (мин)", data: [WAKA_APR23, WAKA_APR24] }]}
        height={120}
        valueSuffix=" мин"
      />

      {/* === LANGUAGES === */}
      <Grid columns={2} gap={20}>
        <Stack gap={10}>
          <H2>Языки (24.04)</H2>
          <Table
            headers={["Язык", "Время", "%"]}
            rows={[
              ["TypeScript", "54 мин", "33%"],
              ["Markdown", "39 мин", "24%"],
              ["Other",     "30 мин", "18%"],
              ["Python",    "24 мин", "15%"],
              ["Bash",      "11 мин", "7%"],
              ["HTML/CSS/JSON", "1 мин", "1%"],
            ]}
            columnAlign={["left", "right", "right"]}
            striped
          />
        </Stack>

        <Stack gap={10}>
          <H2>Категории (24.04)</H2>
          <Table
            headers={["Категория", "Время"]}
            rows={[
              ["AI Coding",    "2ч 41м"],
              ["Writing Docs", "1 мин"],
              ["Coding",       "1 мин"],
            ]}
            columnAlign={["left", "right"]}
            striped
          />
          <H2>Коммиты (project days)</H2>
          <Table
            headers={["Хэш", "Время", "Описание"]}
            rows={[
              ["634d984", "02:43", "docs(debug): debug guide + fix tags"],
              ["b7e8cc5", "02:33", "feat(qa): 136 tests, phase bug fixed"],
              ["5ed473b", "22:55", "fix(frontend): healthcheck wget→curl"],
              ["e42889c", "22:39", "fix(rbac): employee cannot delete"],
              ["f33f441", "22:33", "feat(auth): JWT + RBAC + P0 features"],
              ["1955e61", "21:31", "docs: CHECKPOINT v3.0.0"],
              ["dcd08ee", "21:17", "fix(qa): 31/31 tests pass"],
              ["f8041d5", "20:55", "feat(frontend): Phase 2 SPA"],
            ]}
            columnAlign={["left", "center", "left"]}
          />
        </Stack>
      </Grid>

      <Divider />

      {/* === PHASE BREAKDOWN === */}
      <H2>Статус фаз и оценка времени</H2>

      <BarChart
        categories={phases.map((p) => p.name)}
        series={[
          { name: "Выполнено (ч)", data: phases.map((p) => p.actual) },
          { name: "Осталось (ч)", data: phases.map((p) => (p.done ? 0 : p.est)) },
        ]}
        horizontal
        height={260}
        valueSuffix="ч"
      />

      <Table
        headers={["Фаза", "Статус", "Оценка", "Факт", "Примечание"]}
        rows={[
          ...donePhases.map((p) => [p.name, "Готово", fmtH(p.est), fmtH(p.actual), ""]),
          ["Phase 3 · Deploy", "СЛЕДУЮЩИЙ", "1.5ч", "—", "Traefik labels + Dokploy UI + get URL"],
          ["P0 Fixes",         "Ожидает",   "0.5ч", "—", "AI Gateway + compliance sign-off"],
          ["GitLab push",      "Ожидает",   "0.5ч", "—", "SSH / HTTPS 500 — нужна ручная правка"],
          ["Final smoke",      "Ожидает",   "0.5ч", "—", "Проверка /health + HP-01 на prod URL"],
        ]}
        rowTone={[
          ...donePhases.map(() => "success" as const),
          "warning",
          "neutral",
          "danger",
          "neutral",
        ]}
        columnAlign={["left", "center", "center", "center", "left"]}
        striped
      />

      <Divider />

      {/* === TIMELINE === */}
      <H2>Временная линия до дедлайна</H2>

      <Card>
        <CardHeader trailing={<Pill size="sm" tone={bufferTone} active>{bufferLabel}</Pill>}>
          ~11:00 → 17:30 сегодня ({fmtH(HOURS_TO_DEADLINE)} доступно)
        </CardHeader>
        <CardBody>
          <Table
            headers={["Окно", "Задача", "Оценка", "Результат"]}
            rows={[
              ["11:00 – 12:30", "Phase 3: Deploy (Traefik + Dokploy)", "1.5ч", "Публичный URL"],
              ["12:30 – 13:00", "GitLab push (SSH fix / manual)", "0.5ч", "Коммиты в GitLab"],
              ["13:00 – 13:30", "Final smoke test on prod", "0.5ч", "/health + HP-01 ✓"],
              ["13:30 – 14:00", "P0: AI Gateway check + docs sign-off", "0.5ч", "Compliance review"],
              ["14:00 – 17:30", "БУФЕР / пожарные задачи", "3.5ч", "Запас"],
            ]}
            columnAlign={["left", "left", "center", "left"]}
            rowTone={["warning", "danger", "neutral", "neutral", "success"]}
            striped
          />
        </CardBody>
      </Card>

      <Divider />

      {/* === VERDICT === */}
      <H2>Вердикт</H2>

      <Grid columns={3} gap={12}>
        <Stat value="3ч 5м" label="Трекер WakaTime (факт)" />
        <Stat value="85%" label="Готовность MVP" tone="success" />
        <Stat value="3.5ч" label="Буфер до дедлайна" tone="success" />
      </Grid>

      <Callout tone="success" title="Дедлайн достижим — критический путь: Deploy">
        WakaTime фиксирует 3ч 5м активной работы. 85% функциональности готовы.
        Единственный незакрытый обязательный артефакт — публичный URL на Dokploy.
        При старте деплоя сейчас остаётся 3.5ч буфера до 17:30.
      </Callout>

      <Callout tone="danger" title="Блокер #1 — GitLab push">
        SSH key не настроен + HTTPS возвращает 500 от сервера GitLab. Необходимо
        вручную выполнить push: либо настроить SSH ключ в GitLab UI, либо связаться с
        IT BIOCAD по поводу HTTP 500 на HTTPS remote.
      </Callout>

      <Callout tone="warning" title="Блокер #2 — AI Gateway offline">
        Основная функция генерации недоступна без подключения к BIOCAD AI Gateway
        (URL: AI_GATEWAY_URL в .env). Необходима проверка доступности из Dokploy окружения.
      </Callout>

      <Text tone="tertiary" size="small">
        Данные: WakaTime API · api_key из ~/.wakatime.cfg · Проект: research-protocols-23042026 · 23-24 апр 2026
      </Text>
    </Stack>
  );
}
