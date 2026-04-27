import {
  Stack, Row, Grid, H1, H2, H3, Text, Card, CardHeader, CardBody,
  Pill, Divider, Table, Stat, Callout, Button, Code, useHostTheme,
} from 'cursor/canvas'

// ── RBAC Matrix ─────────────────────────────────────────────────────────────
const ROLES = [
  { role: 'Admin',    tone: 'danger'   as const, perms: ['read','create','update','delete'] },
  { role: 'Employee', tone: 'warning'  as const, perms: ['read','create','update'] },
  { role: 'Auditor',  tone: 'default'  as const, perms: ['read'] },
]

const ALL_ACTIONS = ['read', 'create', 'update', 'delete']

const ACTION_TONE: Record<string, 'success'|'danger'> = {
  read: 'success', create: 'success', update: 'success', delete: 'danger',
}

// ── Nav items ────────────────────────────────────────────────────────────────
const NAV = [
  { label: 'Протоколы', active: true },
  { label: 'Новый протокол', active: false },
]

// ── Protocol list items ──────────────────────────────────────────────────────
const PROTOCOLS = [
  { title: 'BCD-100 Phase II Melanoma', drug: 'BCD-100 · Пролголимаб', phase: 'II', status: 'generated', score: 87 },
  { title: 'BCD-089 Phase III Psoriasis RCT', drug: 'BCD-089 · Иксекизумаб', phase: 'III', status: 'draft', score: null },
  { title: 'BCD-201 Phase I FIH Oncology', drug: 'BCD-201 · Экспериментальный', phase: 'I', status: 'checking', score: null },
]

const STATUS_TONE: Record<string, 'success'|'warning'|'default'> = {
  generated: 'success', draft: 'default', checking: 'warning',
}
const STATUS_LABEL: Record<string, string> = {
  generated: 'Сгенерирован', draft: 'Черновик', checking: 'Проверяется',
}

// ── Protocol detail sections ─────────────────────────────────────────────────
const SECTIONS = [
  'Титульная страница', 'Краткое резюме', 'Введение / Обоснование',
  'Цели исследования', 'Дизайн исследования', 'Популяция', 'Статистика',
]

const AUDIT_ROWS = [
  ['2026-04-23 19:44', 'admin', 'create', 'protocol', 'Создание протокола BCD-100'],
  ['2026-04-23 19:46', 'employee', 'ai_generate', 'protocol', 'AI-генерация v1 · 3 241 ms'],
  ['2026-04-23 19:47', 'employee', 'consistency_check', 'protocol', 'Score 87 · 3 замечания'],
  ['2026-04-23 19:50', 'auditor', 'read', 'protocol', 'Просмотр протокола'],
  ['2026-04-23 19:55', 'admin', 'delete', 'protocol', 'Удаление BCD-201 FIH'],
]

export default function UIPreview() {
  const { tokens } = useHostTheme()

  const surf = tokens.surfaceBackground
  const border = tokens.borderSubtle
  const accent = tokens.accentForeground
  const fg = tokens.textPrimary
  const fgSec = tokens.textSecondary
  const fgMut = tokens.textMuted

  const headerBg = tokens.surfaceRaised

  return (
    <Stack gap={32} style={{ padding: '24px 28px', maxWidth: 1100, margin: '0 auto' }}>

      {/* Title */}
      <Row gap={12} style={{ alignItems: 'baseline' }}>
        <H1>AI Protocol Generator — UI Preview</H1>
        <Pill tone="default" size="sm">v0.2.0</Pill>
      </Row>

      {/* ── RBAC ───────────────────────────────────────────────────────────── */}
      <section>
        <H2>Ролевая модель (RBAC)</H2>
        <Text tone="secondary" size="small" style={{ marginBottom: 16 }}>
          Employee: read, create, update — delete убран. Admin: полный доступ. Auditor: только чтение.
        </Text>
        <Grid columns={3} gap={12}>
          {ROLES.map(({ role, tone, perms }) => (
            <Card key={role} size="sm" variant="outlined">
              <CardHeader>
                <Row gap={8} style={{ alignItems: 'center' }}>
                  <Text weight="semibold">{role}</Text>
                  <Pill tone={tone} size="sm">{role}</Pill>
                </Row>
              </CardHeader>
              <CardBody>
                <Stack gap={6}>
                  {ALL_ACTIONS.map(act => {
                    const allowed = perms.includes(act)
                    return (
                      <Row key={act} gap={8} style={{ alignItems: 'center' }}>
                        <span style={{
                          width: 8, height: 8, borderRadius: '50%',
                          background: allowed
                            ? (act === 'delete' ? tokens.accentForeground : tokens.successForeground)
                            : tokens.borderSubtle,
                          flexShrink: 0,
                        }} />
                        <Text
                          size="small"
                          tone={allowed ? 'default' : 'muted'}
                          style={{ textDecoration: allowed ? undefined : 'line-through' }}
                        >
                          {act}
                        </Text>
                        {act === 'delete' && allowed && (
                          <Pill tone="danger" size="sm">admin only</Pill>
                        )}
                      </Row>
                    )
                  })}
                </Stack>
              </CardBody>
            </Card>
          ))}
        </Grid>
      </section>

      <Divider />

      {/* ── App Header ─────────────────────────────────────────────────────── */}
      <section>
        <H2>Шапка приложения</H2>

        <div style={{
          background: headerBg,
          border: `1px solid ${border}`,
          borderRadius: 8,
          padding: '12px 20px',
        }}>
          <Row gap={0} style={{ alignItems: 'center', justifyContent: 'space-between' }}>
            {/* Logo */}
            <Row gap={10} style={{ alignItems: 'center' }}>
              <div style={{
                width: 36, height: 36, borderRadius: 8,
                background: accent,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <span style={{ color: '#fff', fontWeight: 700, fontSize: 14 }}>AI</span>
              </div>
              <Stack gap={0}>
                <Text weight="semibold" size="small">AI Protocol Generator</Text>
                <Text tone="muted" size="small">Qwen3.5-122B · GCP/ICH · FOR REVIEW ONLY</Text>
              </Stack>
            </Row>

            {/* Nav */}
            <Row gap={4} style={{ alignItems: 'center' }}>
              {NAV.map(({ label, active }) => (
                <div key={label} style={{
                  padding: '6px 12px', borderRadius: 6,
                  background: active ? `${accent}18` : 'transparent',
                  cursor: 'pointer',
                }}>
                  <Text size="small" weight={active ? 'semibold' : 'normal'}
                    style={{ color: active ? accent : fgSec }}>
                    {label}
                  </Text>
                </div>
              ))}

              {/* User badge */}
              <Row gap={6} style={{
                marginLeft: 12, paddingLeft: 12,
                borderLeft: `1px solid ${border}`,
                alignItems: 'center',
              }}>
                <div style={{
                  width: 24, height: 24, borderRadius: '50%',
                  background: border, display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <Text size="small" tone="muted">A</Text>
                </div>
                <Text size="small" weight="semibold">admin</Text>
                <Pill tone="danger" size="sm">Admin</Pill>
                <Text size="small" tone="muted" style={{ cursor: 'pointer' }}>Выйти</Text>
              </Row>
            </Row>
          </Row>
        </div>
      </section>

      {/* ── Login Page ─────────────────────────────────────────────────────── */}
      <section>
        <H2>Страница входа</H2>
        <Grid columns={2} gap={16}>
          {/* Login form */}
          <Card size="sm" variant="outlined">
            <CardHeader>Вход в систему</CardHeader>
            <CardBody>
              <Stack gap={10}>
                <Stack gap={4}>
                  <Text size="small" weight="semibold">Логин</Text>
                  <div style={{
                    border: `1px solid ${border}`, borderRadius: 6,
                    padding: '7px 10px', background: surf,
                  }}>
                    <Text size="small" tone="muted">admin / employee / auditor</Text>
                  </div>
                </Stack>
                <Stack gap={4}>
                  <Text size="small" weight="semibold">Пароль</Text>
                  <div style={{
                    border: `1px solid ${border}`, borderRadius: 6,
                    padding: '7px 10px', background: surf,
                  }}>
                    <Text size="small" tone="muted">••••••••</Text>
                  </div>
                </Stack>
                <div style={{
                  background: accent, color: '#fff', borderRadius: 6,
                  padding: '8px 14px', textAlign: 'center', cursor: 'pointer',
                }}>
                  <Text size="small" weight="semibold" style={{ color: '#fff' }}>Войти</Text>
                </div>
              </Stack>
            </CardBody>
          </Card>

          {/* Demo users */}
          <Card size="sm" variant="outlined">
            <CardHeader>Демо-пользователи</CardHeader>
            <CardBody>
              <Stack gap={8}>
                {[
                  { u: 'admin',    p: 'admin123',    role: 'Admin',    tone: 'danger'   as const },
                  { u: 'employee', p: 'employee123', role: 'Employee', tone: 'warning'  as const },
                  { u: 'auditor',  p: 'auditor123',  role: 'Auditor',  tone: 'default'  as const },
                ].map(({ u, p, role, tone }) => (
                  <Row key={u} gap={8} style={{
                    alignItems: 'center', padding: '6px 8px',
                    border: `1px solid ${border}`, borderRadius: 6,
                  }}>
                    <Code>{u} / {p}</Code>
                    <Pill tone={tone} size="sm">{role}</Pill>
                  </Row>
                ))}
                <Text size="small" tone="muted">Нажмите на строку для автозаполнения</Text>
              </Stack>
            </CardBody>
          </Card>
        </Grid>
      </section>

      <Divider />

      {/* ── Protocol List ──────────────────────────────────────────────────── */}
      <section>
        <Row gap={0} style={{ alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <H2>Список протоколов</H2>
          <Row gap={8}>
            <div style={{
              border: `1px solid ${border}`, borderRadius: 6,
              padding: '5px 12px',
            }}>
              <Text size="small" tone="muted">Все фазы</Text>
            </div>
            <div style={{
              background: accent, borderRadius: 6, padding: '5px 12px', cursor: 'pointer',
            }}>
              <Text size="small" weight="semibold" style={{ color: '#fff' }}>+ Новый</Text>
            </div>
          </Row>
        </Row>

        <Stack gap={8}>
          {PROTOCOLS.map(({ title, drug, phase, status, score }) => (
            <div key={title} style={{
              border: `1px solid ${border}`, borderRadius: 8,
              padding: '14px 16px',
              background: surf,
              cursor: 'pointer',
            }}>
              <Row gap={0} style={{ alignItems: 'center', justifyContent: 'space-between' }}>
                <Stack gap={4}>
                  <Row gap={8} style={{ alignItems: 'center' }}>
                    <Text weight="semibold">{title}</Text>
                    <Pill tone="default" size="sm">Phase {phase}</Pill>
                    <Pill tone={STATUS_TONE[status]} size="sm">{STATUS_LABEL[status]}</Pill>
                  </Row>
                  <Text size="small" tone="muted">{drug}</Text>
                </Stack>
                {score && (
                  <Stack gap={2} style={{ alignItems: 'flex-end' }}>
                    <Text size="small" tone="muted">GCP Score</Text>
                    <Text weight="semibold" style={{ color: tokens.successForeground }}>{score}%</Text>
                  </Stack>
                )}
              </Row>
            </div>
          ))}
        </Stack>
      </section>

      <Divider />

      {/* ── Protocol Page Detail ───────────────────────────────────────────── */}
      <section>
        <H2>Страница протокола</H2>
        <Grid columns={12} gap={14}>
          {/* Sidebar */}
          <div style={{ gridColumn: 'span 3' }}>
            <Card size="sm" variant="outlined">
              <CardHeader>Разделы</CardHeader>
              <CardBody>
                <Stack gap={4}>
                  {SECTIONS.map((s, i) => (
                    <div key={s} style={{
                      padding: '5px 8px', borderRadius: 5,
                      background: i === 0 ? `${accent}15` : 'transparent',
                    }}>
                      <Text size="small"
                        style={{ color: i === 0 ? accent : fgSec }}
                        weight={i === 0 ? 'semibold' : 'normal'}
                      >
                        {s}
                      </Text>
                    </div>
                  ))}
                </Stack>
                <Divider />
                <Stack gap={6}>
                  <Text size="small" tone="muted">Версия</Text>
                  <div style={{
                    border: `1px solid ${border}`, borderRadius: 5,
                    padding: '5px 8px',
                  }}>
                    <Text size="small">v1 · AI-generated v1</Text>
                  </div>
                  <div>
                    <Text size="small" tone="muted">GCP Score: </Text>
                    <Text size="small" weight="semibold" style={{ color: tokens.successForeground }}>87%</Text>
                  </div>
                </Stack>
              </CardBody>
            </Card>
          </div>

          {/* Content + Controls */}
          <div style={{ gridColumn: 'span 9' }}>
            <Stack gap={10}>
              {/* Action bar */}
              <div style={{
                border: `1px solid ${border}`, borderRadius: 8,
                padding: '10px 14px', background: surf,
              }}>
                <Row gap={0} style={{ alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
                  <Stack gap={2}>
                    <Row gap={8} style={{ alignItems: 'center' }}>
                      <Text weight="semibold">BCD-100 Phase II Melanoma</Text>
                      <Pill tone="success" size="sm">Сгенерирован</Pill>
                    </Row>
                    <Text size="small" tone="muted">BCD-100 · Пролголимаб · oncology</Text>
                  </Stack>
                  <Row gap={6} style={{ flexWrap: 'wrap' }}>
                    <div style={{
                      background: accent, borderRadius: 6, padding: '5px 12px',
                    }}>
                      <Text size="small" weight="semibold" style={{ color: '#fff' }}>Генерировать</Text>
                    </div>
                    <div style={{
                      border: `1px solid ${border}`, borderRadius: 6, padding: '5px 10px',
                    }}>
                      <Text size="small">GCP-проверка</Text>
                    </div>
                    <Row gap={4}>
                      {['md','html','docx'].map(fmt => (
                        <div key={fmt} style={{
                          border: `1px solid ${border}`, borderRadius: 5,
                          padding: '4px 8px',
                        }}>
                          <Text size="small" style={{ textTransform: 'uppercase', fontSize: 10 }}>{fmt}</Text>
                        </div>
                      ))}
                    </Row>
                    <Callout tone="warning" style={{ padding: '4px 10px' }}>
                      <Text size="small" tone="muted">Delete — только Admin</Text>
                    </Callout>
                  </Row>
                </Row>
              </div>

              {/* Comment input */}
              <div style={{
                border: `1px solid ${border}`, borderRadius: 8,
                padding: '10px 14px', background: surf,
              }}>
                <Text size="small" weight="semibold" style={{ marginBottom: 4 }}>Комментарий к версии</Text>
                <div style={{
                  border: `1px solid ${border}`, borderRadius: 5, padding: '6px 10px',
                }}>
                  <Text size="small" tone="muted">Описание изменений...</Text>
                </div>
              </div>

              {/* Section content preview */}
              <div style={{
                border: `1px solid ${border}`, borderRadius: 8,
                padding: '16px', background: surf,
              }}>
                <Row gap={0} style={{
                  alignItems: 'center', justifyContent: 'space-between', marginBottom: 12,
                }}>
                  <Row gap={6} style={{ alignItems: 'center' }}>
                    <div style={{
                      width: 4, height: 16, borderRadius: 2, background: accent,
                    }} />
                    <Text weight="semibold">Титульная страница</Text>
                  </Row>
                  <div style={{
                    border: `1px solid ${border}`, borderRadius: 5,
                    padding: '3px 8px', cursor: 'pointer',
                  }}>
                    <Text size="small" tone="muted">Перегенерировать</Text>
                  </div>
                </Row>

                <Stack gap={6}>
                  <Text size="small" weight="semibold">
                    BCD-100 в лечении метастатической меланомы — Фаза II открытое исследование
                  </Text>
                  <Text size="small" tone="secondary">
                    Спонсор: BIOCAD · Протокол № BCD-100-2/2026 · Версия 1.0 · Апрель 2026
                  </Text>
                  <Text size="small" tone="muted">
                    Рандомизированное открытое исследование эффективности и безопасности пролголимаба
                    у пациентов с метастатической меланомой, прогрессировавших после 1-й линии терапии...
                  </Text>
                  <div style={{
                    marginTop: 4, padding: '6px 10px',
                    background: `${tokens.warningForeground}12`,
                    borderRadius: 5,
                    borderLeft: `3px solid ${tokens.warningForeground}`,
                  }}>
                    <Text size="small" tone="muted">
                      FOR DEMONSTRATION PURPOSES ONLY — SYNTHETIC DATA · AI-Assisted. Requires qualified person review.
                    </Text>
                  </div>
                </Stack>
              </div>
            </Stack>
          </div>
        </Grid>
      </section>

      <Divider />

      {/* ── Audit Trail ────────────────────────────────────────────────────── */}
      <section>
        <H2>Audit Trail — кто, где, когда, зачем</H2>
        <Text tone="secondary" size="small" style={{ marginBottom: 12 }}>
          Все действия логируются в audit_log с performed_by (username), role, action, entity_id, timestamp
        </Text>
        <Table
          headers={['Время', 'Пользователь', 'Действие', 'Объект', 'Детали']}
          rows={AUDIT_ROWS}
          rowTone={[undefined, undefined, undefined, undefined, 'danger']}
        />
      </section>

      <Divider />

      {/* ── API Endpoints ──────────────────────────────────────────────────── */}
      <section>
        <H2>Новые API Endpoints (сессия 4)</H2>
        <Grid columns={2} gap={16}>
          <Stack gap={8}>
            <H3>Аутентификация</H3>
            <Stack gap={6}>
              {[
                { m: 'POST', p: '/api/v1/auth/token', d: 'Login, получить JWT' },
                { m: 'GET',  p: '/api/v1/auth/me',    d: 'Текущий пользователь' },
              ].map(({ m, p, d }) => (
                <Row key={p} gap={8} style={{ alignItems: 'center' }}>
                  <Pill tone={m === 'POST' ? 'warning' : 'default'} size="sm">{m}</Pill>
                  <Code style={{ fontSize: 11 }}>{p}</Code>
                  <Text size="small" tone="muted">{d}</Text>
                </Row>
              ))}
            </Stack>

            <H3>Регенерация секций (FR-03.5)</H3>
            <Row gap={8} style={{ alignItems: 'center' }}>
              <Pill tone="warning" size="sm">POST</Pill>
              <Code style={{ fontSize: 10 }}>/protocols/{'{id}'}/sections/{'{key}'}/regenerate</Code>
            </Row>
            <Text size="small" tone="muted">Перегенерирует одну секцию, создаёт новую версию</Text>
          </Stack>

          <Stack gap={8}>
            <H3>RBAC матрица (HTTP responses)</H3>
            <Table
              headers={['Роль', 'DELETE /protocols', 'POST /generate', 'GET /protocols']}
              rows={[
                ['Admin',    '204 No Content', '202 Accepted', '200 OK'],
                ['Employee', '403 Forbidden',  '202 Accepted', '200 OK'],
                ['Auditor',  '403 Forbidden',  '403 Forbidden','200 OK'],
              ]}
              rowTone={[undefined, 'warning', 'danger']}
            />
          </Stack>
        </Grid>
      </section>

      {/* Footer */}
      <Divider />
      <Row gap={0} style={{ alignItems: 'center', justifyContent: 'space-between' }}>
        <Text size="small" tone="muted">
          AI Protocol Generator v0.2.0 · 42/42 tests · FOR RESEARCH USE ONLY
        </Text>
        <Text size="small" tone="muted">InHouse/Qwen3.5-122B · GCP/ICH E6(R2)</Text>
      </Row>

    </Stack>
  )
}
