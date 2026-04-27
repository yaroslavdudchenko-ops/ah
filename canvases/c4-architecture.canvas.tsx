import {
  computeDAGLayout,
  H1, H2, Text, Stack, Row, Divider, Button, Callout,
  useHostTheme, useCanvasState,
} from 'cursor/canvas';

type NodeKind = 'system' | 'user' | 'db' | 'ai' | 'component' | 'external' | 'infra';

interface NodeMeta {
  label: string;
  sublabel?: string;
  kind: NodeKind;
}

interface DiagramDef {
  title: string;
  description: string;
  nodes: Array<{ id: string }>;
  edges: Array<{ from: string; to: string; label?: string }>;
  meta: Record<string, NodeMeta>;
  direction?: 'vertical' | 'horizontal';
  nodeWidth?: number;
}

const DIAGRAMS: DiagramDef[] = [
  {
    title: 'L1 — System Context',
    description: 'Внешние акторы и системы, с которыми взаимодействует AI Protocol Generator.',
    direction: 'vertical',
    nodeWidth: 170,
    nodes: [
      { id: 'researcher' }, { id: 'reviewer' },
      { id: 'system' },
      { id: 'gateway' }, { id: 'gitlab' }, { id: 'dokploy' },
    ],
    edges: [
      { from: 'researcher', to: 'system', label: 'создаёт протокол' },
      { from: 'reviewer', to: 'system', label: 'ревьюирует' },
      { from: 'system', to: 'gateway', label: 'POST /v1/chat/completions' },
      { from: 'system', to: 'gitlab', label: 'git push' },
      { from: 'dokploy', to: 'gitlab', label: 'git clone on deploy' },
    ],
    meta: {
      researcher: { label: 'Исследователь', sublabel: 'Клинический учёный', kind: 'user' },
      reviewer: { label: 'Мед. ревьюер', sublabel: 'Валидация протокола', kind: 'user' },
      system: { label: 'AI Protocol Generator', sublabel: 'Web Application', kind: 'system' },
      gateway: { label: 'AI Gateway', sublabel: 'InHouse/Qwen3.5-122B', kind: 'ai' },
      gitlab: { label: 'GitLab', sublabel: 'gitlab.biocad.ru', kind: 'external' },
      dokploy: { label: 'Dokploy', sublabel: 'Deploy platform', kind: 'external' },
    },
  },
  {
    title: 'L2 — Containers',
    description: 'Docker-контейнеры внутри системы и их связи.',
    direction: 'vertical',
    nodeWidth: 170,
    nodes: [
      { id: 'user' },
      { id: 'traefik' },
      { id: 'frontend' }, { id: 'backend' },
      { id: 'db' }, { id: 'gateway' },
    ],
    edges: [
      { from: 'user', to: 'traefik', label: 'HTTPS' },
      { from: 'traefik', to: 'frontend', label: 'static files' },
      { from: 'traefik', to: 'backend', label: '/api/* proxy' },
      { from: 'frontend', to: 'backend', label: 'REST API' },
      { from: 'backend', to: 'db', label: 'asyncpg TCP:5432' },
      { from: 'backend', to: 'gateway', label: 'HTTPS/JSON' },
    ],
    meta: {
      user: { label: 'Пользователь', kind: 'user' },
      traefik: { label: 'Traefik', sublabel: 'Reverse proxy', kind: 'infra' },
      frontend: { label: 'frontend', sublabel: 'React/Vite · nginx:alpine', kind: 'component' },
      backend: { label: 'backend', sublabel: 'FastAPI · python:3.12-slim', kind: 'system' },
      db: { label: 'db', sublabel: 'postgres:16-alpine · JSONB', kind: 'db' },
      gateway: { label: 'AI Gateway', sublabel: 'InHouse/Qwen3.5-122B', kind: 'ai' },
    },
  },
  {
    title: 'L3 — Backend Components',
    description: 'Внутренние компоненты контейнера Backend (v1.2.0 · 30+ эндпоинтов · 10 роутеров). PostgreSQL и AI Gateway — внешние контейнеры из L2.',
    direction: 'vertical',
    nodeWidth: 180,
    nodes: [
      { id: 'api_protocols' }, { id: 'api_generate' }, { id: 'api_check' }, { id: 'api_export' },
      { id: 'api_auth' }, { id: 'api_audit' }, { id: 'api_templates' }, { id: 'api_biocad' }, { id: 'api_embeddings' },
      { id: 'svc_generator' }, { id: 'svc_consistency' }, { id: 'svc_export' }, { id: 'svc_embedding' },
      { id: 'ai_client' }, { id: 'models' },
      { id: 'ext_db' }, { id: 'ext_gateway' },
    ],
    edges: [
      { from: 'api_protocols', to: 'models' },
      { from: 'api_generate', to: 'svc_generator' },
      { from: 'api_check', to: 'svc_consistency' },
      { from: 'api_export', to: 'svc_export' },
      { from: 'api_audit', to: 'models' },
      { from: 'api_templates', to: 'models' },
      { from: 'api_biocad', to: 'ext_gateway' },
      { from: 'api_embeddings', to: 'svc_embedding' },
      { from: 'svc_generator', to: 'ai_client' },
      { from: 'svc_generator', to: 'svc_embedding', label: 'RAG (opt)' },
      { from: 'svc_consistency', to: 'ai_client' },
      { from: 'svc_generator', to: 'models' },
      { from: 'svc_embedding', to: 'models' },
      { from: 'models', to: 'ext_db', label: 'asyncpg' },
      { from: 'ai_client', to: 'ext_gateway', label: 'HTTPS' },
    ],
    meta: {
      api_protocols: { label: 'ProtocolsRouter', sublabel: 'CRUDL + 4-eyes + diff + copy', kind: 'component' },
      api_generate:  { label: 'GenerateRouter',  sublabel: 'POST /generate + section regen', kind: 'component' },
      api_check:     { label: 'CheckRouter',     sublabel: 'POST /check (GCP/ICH)', kind: 'component' },
      api_export:    { label: 'ExportRouter',    sublabel: 'GET /export + open-issues', kind: 'component' },
      api_auth:      { label: 'AuthRouter',      sublabel: 'POST /token · GET /me', kind: 'component' },
      api_audit:     { label: 'AuditRouter',     sublabel: 'GET /audit · GET /{id}/audit', kind: 'component' },
      api_templates: { label: 'TemplatesRouter', sublabel: 'GET /templates (Phase I/II/III)', kind: 'component' },
      api_biocad:    { label: 'BiocadTrialsRouter', sublabel: 'GET /biocad-trials (прокси)', kind: 'component' },
      api_embeddings:{ label: 'EmbeddingsRouter', sublabel: 'GET /status · POST /reindex', kind: 'component' },
      svc_generator: { label: 'ProtocolGenerator', sublabel: '12 секций + SAP/ICF + RAG', kind: 'system' },
      svc_consistency:{ label: 'ConsistencyChecker', sublabel: 'GCP/ICH + РФ НМД score', kind: 'system' },
      svc_export:    { label: 'ExportService',   sublabel: 'DOCX / HTML / MD + Issues CSV', kind: 'component' },
      svc_embedding: { label: 'EmbeddingService', sublabel: 'JSONB vectors · similarity', kind: 'component' },
      ai_client:     { label: 'AIGatewayClient', sublabel: 'httpx + tenacity ×3 + prompt_guard', kind: 'ai' },
      models:        { label: 'SQLAlchemy Models', sublabel: 'Protocol · Version · AuditLog · Embeddings', kind: 'component' },
      ext_db:        { label: '[Container] PostgreSQL 16', sublabel: 'db — внешний контейнер L2', kind: 'external' },
      ext_gateway:   { label: '[Container] AI Gateway', sublabel: 'InHouse/Qwen3.5-122B — внешний', kind: 'external' },
    },
  },
  {
    title: 'Deploy Flow',
    description: 'Процесс деплоя: GitLab → Dokploy → Docker Compose.',
    direction: 'horizontal',
    nodeWidth: 160,
    nodes: [
      { id: 'dev' }, { id: 'gitlab' }, { id: 'dokploy' }, { id: 'compose' },
      { id: 'frontend' }, { id: 'backend' }, { id: 'db' },
    ],
    edges: [
      { from: 'dev', to: 'gitlab', label: 'git push' },
      { from: 'gitlab', to: 'dokploy', label: 'webhook' },
      { from: 'dokploy', to: 'compose', label: 'docker compose up' },
      { from: 'compose', to: 'frontend', label: 'nginx:alpine' },
      { from: 'compose', to: 'backend', label: 'python:3.12-slim' },
      { from: 'compose', to: 'db', label: 'postgres:16-alpine' },
    ],
    meta: {
      dev: { label: 'Developer', sublabel: 'Local machine', kind: 'user' },
      gitlab: { label: 'GitLab', sublabel: 'gitlab.biocad.ru', kind: 'external' },
      dokploy: { label: 'Dokploy', sublabel: 'Auto-deploy', kind: 'infra' },
      compose: { label: 'Docker Compose', sublabel: 'docker-compose.yml', kind: 'infra' },
      frontend: { label: 'frontend', sublabel: ':80', kind: 'component' },
      backend: { label: 'backend', sublabel: ':8000', kind: 'component' },
      db: { label: 'db', sublabel: ':5432 + db-data volume', kind: 'db' },
    },
  },
];

const TABS = ['L1 Контекст', 'L2 Контейнеры', 'L3 Компоненты', 'Deploy'];

const NODE_H = 54;

interface DiagramSVGProps {
  diagram: DiagramDef;
  theme: ReturnType<typeof useHostTheme>;
}

function DiagramSVG({ diagram, theme }: DiagramSVGProps) {
  const nw = diagram.nodeWidth ?? 160;
  const layout = computeDAGLayout({
    nodes: diagram.nodes,
    edges: diagram.edges,
    direction: diagram.direction || 'vertical',
    nodeWidth: nw,
    nodeHeight: NODE_H,
    rankGap: 90,
    nodeGap: 56,
    padding: 32,
  });

  const edgeLabelMap = new Map(
    diagram.edges.map(e => [`${e.from}--${e.to}`, e.label ?? ''])
  );

  function nodeColors(kind: NodeKind) {
    switch (kind) {
      case 'system':
        return { fill: theme.accent.control, stroke: theme.accent.primary, text: theme.text.onAccent, sw: 2 };
      case 'ai':
        return { fill: theme.fill.primary, stroke: theme.accent.primary, text: theme.text.primary, sw: 2 };
      case 'db':
        return { fill: theme.fill.secondary, stroke: theme.stroke.primary, text: theme.text.primary, sw: 1 };
      case 'user':
        return { fill: theme.bg.elevated, stroke: theme.stroke.secondary, text: theme.text.secondary, sw: 1 };
      case 'external':
        return { fill: theme.fill.tertiary, stroke: theme.stroke.secondary, text: theme.text.secondary, sw: 1 };
      case 'infra':
        return { fill: theme.fill.secondary, stroke: theme.stroke.primary, text: theme.text.primary, sw: 1 };
      case 'component':
      default:
        return { fill: theme.bg.elevated, stroke: theme.stroke.primary, text: theme.text.primary, sw: 1 };
    }
  }

  const markerId = `arrow-${diagram.title.replace(/\s+/g, '')}`;

  return (
    <svg width={layout.width} height={layout.height} style={{ display: 'block', maxWidth: '100%' }}>
      <defs>
        <marker id={markerId} markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
          <polygon points="0 0, 8 3, 0 6" style={{ fill: theme.stroke.secondary }} />
        </marker>
      </defs>

      {layout.edges.map((edge, i) => {
        const label = edgeLabelMap.get(`${edge.from}--${edge.to}`) ?? '';
        const toMeta = diagram.meta[edge.to];
        const isAi = toMeta?.kind === 'ai';
        const midX = (edge.sourceX + edge.targetX) / 2;
        const midY = (edge.sourceY + edge.targetY) / 2;
        return (
          <g key={i}>
            <line
              x1={edge.sourceX} y1={edge.sourceY}
              x2={edge.targetX} y2={edge.targetY}
              markerEnd={`url(#${markerId})`}
              style={{
                stroke: isAi ? theme.accent.primary : theme.stroke.secondary,
                strokeWidth: isAi ? 1.5 : 1,
                strokeDasharray: edge.isBackEdge ? '5 4' : undefined,
              }}
            />
            {label && (
              <text x={midX} y={midY - 5} textAnchor="middle"
                style={{ fill: theme.text.tertiary, fontSize: 9, fontFamily: 'inherit' }}>
                {label}
              </text>
            )}
          </g>
        );
      })}

      {layout.nodes.map(node => {
        const meta = diagram.meta[node.id];
        if (!meta) return null;
        const c = nodeColors(meta.kind);
        return (
          <g key={node.id}>
            <rect
              x={node.x} y={node.y} width={nw} height={NODE_H} rx={6}
              style={{ fill: c.fill, stroke: c.stroke, strokeWidth: c.sw }}
            />
            <text
              x={node.x + nw / 2}
              y={node.y + NODE_H / 2 + (meta.sublabel ? -9 : 0)}
              textAnchor="middle" dominantBaseline="middle"
              style={{ fill: c.text, fontSize: 11, fontWeight: '600', fontFamily: 'inherit' }}
            >
              {meta.label}
            </text>
            {meta.sublabel && (
              <text
                x={node.x + nw / 2}
                y={node.y + NODE_H / 2 + 10}
                textAnchor="middle" dominantBaseline="middle"
                style={{ fill: theme.text.tertiary, fontSize: 9, fontFamily: 'inherit' }}
              >
                {meta.sublabel}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

const LEGEND_ITEMS: Array<{ kind: NodeKind; label: string }> = [
  { kind: 'system', label: 'Наша система' },
  { kind: 'ai', label: 'AI Gateway (только локальный)' },
  { kind: 'component', label: 'Компонент' },
  { kind: 'db', label: 'База данных' },
  { kind: 'infra', label: 'Инфраструктура' },
  { kind: 'external', label: 'Внешняя система' },
  { kind: 'user', label: 'Актор' },
];

export default function C4Architecture() {
  const [activeTab, setActiveTab] = useCanvasState<number>('tab', 0);
  const theme = useHostTheme();
  const diagram = DIAGRAMS[activeTab];

  function legendColor(kind: NodeKind) {
    switch (kind) {
      case 'system': return { bg: theme.accent.control, border: theme.accent.primary };
      case 'ai': return { bg: theme.fill.primary, border: theme.accent.primary };
      case 'db': return { bg: theme.fill.secondary, border: theme.stroke.primary };
      case 'external': return { bg: theme.fill.tertiary, border: theme.stroke.secondary };
      case 'infra': return { bg: theme.fill.secondary, border: theme.stroke.primary };
      default: return { bg: theme.bg.elevated, border: theme.stroke.primary };
    }
  }

  return (
    <Stack gap={20} style={{ padding: 28 }}>
      <Stack gap={4}>
        <H1>C4 Architecture</H1>
        <Text tone="secondary">AI Protocol Generator · v1.2.0 · 2026-04-24 · CHECKPOINT v12.0.0 · 10 роутеров · 30+ эндпоинтов</Text>
      </Stack>

      <Callout tone="info">
        AI-провайдер: <strong>только внутренний AI Gateway</strong> (InHouse/Qwen3.5-122B).
        Внешние LLM (OpenRouter, OpenAI, Anthropic) запрещены политикой ИБ (NFR-08 / ADR-002 v2.0).
      </Callout>

      <Row gap={8} style={{ flexWrap: 'wrap' }}>
        {TABS.map((tab, i) => (
          <Button key={tab} onClick={() => setActiveTab(i)}>
            {activeTab === i ? `▶ ${tab}` : tab}
          </Button>
        ))}
      </Row>

      <Divider />

      <Stack gap={6}>
        <H2>{diagram.title}</H2>
        <Text tone="secondary">{diagram.description}</Text>
      </Stack>

      <div style={{ overflowX: 'auto', overflowY: 'auto', borderRadius: 6,
        border: `1px solid ${theme.stroke.secondary}`, padding: 16, background: theme.bg.editor }}>
        <DiagramSVG diagram={diagram} theme={theme} />
      </div>

      <Divider />

      <H2>Легенда</H2>
      <Row gap={16} style={{ flexWrap: 'wrap', alignItems: 'center' }}>
        {LEGEND_ITEMS.map(({ kind, label }) => {
          const c = legendColor(kind);
          return (
            <Row key={kind} gap={6} style={{ alignItems: 'center' }}>
              <div style={{
                width: 12, height: 12, borderRadius: 3,
                background: c.bg,
                border: `1.5px solid ${c.border}`,
                flexShrink: 0,
              }} />
              <Text size="small" tone="secondary">{label}</Text>
            </Row>
          );
        })}
      </Row>

      <Divider />

      <Stack gap={6}>
        <H2>Ключевые ограничения</H2>
        <Text size="small" tone="secondary">
          <strong>C4 L3:</strong> показывает только внутренние компоненты контейнера Backend.
          PostgreSQL и AI Gateway — контейнеры L2, отображаются как внешняя граница (серый узел) для обозначения зависимостей.
        </Text>
        <Text size="small" tone="secondary">
          <strong>NFR-08:</strong> данные протоколов КИ передаются исключительно во внутренний AI Gateway.
          При недоступности Gateway → HTTP 503 (не fallback на внешние LLM).
        </Text>
        <Text size="small" tone="secondary">
          <strong>Docker:</strong> без container_name · short port syntax · named volumes · non-root user · HEALTHCHECK.
        </Text>
        <Text size="small" tone="secondary">
          <strong>API:</strong> CRUDL-complete · snake_case naming · error shape: &#123;"error":&#123;"code","message","details"&#125;&#125;.
        </Text>
      </Stack>
    </Stack>
  );
}
