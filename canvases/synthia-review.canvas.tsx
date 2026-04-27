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

const CATEGORIES = [
  {
    id: "value",
    label: "Total Value",
    score: 7.5,
    tone: "success" as const,
    justification:
      "Clear, specific problem domain with genuine compliance burden addressed. Immediate utility for BIOCAD clinical teams. Open Issues export (JSON/CSV), SAP/ICF artifacts, Governance workflow and Audit trail significantly increase delivery value over initial MVP scope.",
    strengths: [
      "Addresses real regulatory burden (61-ФЗ, ICH E6 R2, GCP ЕАЭС, Решение №77)",
      "RBAC + audit trail satisfies GCP traceability requirements for regulated environments",
      "DOCX export + Open Issues JSON/CSV make AI output immediately usable in clinical workflows",
      "SAP (Appendix A) and ICF (Appendix B) go beyond MVP scope — rare in protocol tools",
      "4-eyes governance and lock-after-approve provide compliance-ready review workflow",
    ],
    weaknesses: [
      "AI Gateway offline in local dev — core value proposition needs BIOCAD network access",
      "No integration with existing clinical systems (ct.biocad.ru deferred to post-MVP)",
      "RAG Phase 1 implemented but disabled (AI_EMBEDDING_URL not set) — no institutional memory yet",
      "Single-org MVP; no multi-tenant or SaaS path defined",
    ],
    improvement:
      "Establish a dev/staging AI Gateway instance (Ollama or BIOCAD staging) so the core generation flow can be validated end-to-end before stakeholder delivery.",
  },
  {
    id: "style",
    label: "Style",
    score: 7.0,
    tone: "info" as const,
    justification:
      "Clean, purposeful design with strong brand identity. CreateProtocolPage.tsx with AutocompleteField and CriteriaList improves UX for complex clinical data entry. SVG morphing orb and Synthia branding add character.",
    strengths: [
      "Cohesive 'Synthia' brand with custom SVG morphing animation during generation",
      "CreateProtocolPage.tsx: AutocompleteField for drug/inn/indication, CriteriaList for inclusion/exclusion",
      "Status badges, colored tag chips, audit trail — all polished and professional",
      "Diff viewer (color-coded, section-level) enables clear protocol change review",
      "Draft modal gives an immersive, print-ready full protocol preview",
    ],
    weaknesses: [
      "No mobile/responsive design explicitly verified — clinical users may use tablets",
      "UI exclusively in Russian — no i18n strategy for international stakeholders",
      "No loading skeletons or empty states — blank screens during slow generation",
    ],
    improvement:
      "Add loading skeletons to the protocol list and generation status polling. This reduces perceived wait time for the highest-traffic flow in the app.",
  },
  {
    id: "innovation",
    label: "Innovation",
    score: 7.5,
    tone: "success" as const,
    justification:
      "AI-driven GCP-compliant protocol generation is genuinely novel in the Russian pharma space. Internal-only LLM with RAG Phase 1 (JSONB vectors) is architecturally forward-looking. SAP/ICF generation covers statistical analysis and informed consent — rarely automated.",
    strengths: [
      "Internal-only AI Gateway (Qwen3.5-122B) — zero data-leak risk, compliant with NFR-08",
      "Dual compliance scoring (ICH E6 R2 + РФ НМД) adds tangible, differentiating value",
      "SAP Appendix A: ITT/PP/Safety populations, power analysis, MCAR/MAR/MNAR handling",
      "RAG Phase 1: JSONB embeddings + similarity search in existing PostgreSQL (zero extra infra)",
      "Section-by-section generation + regen enables incremental clinical review",
    ],
    weaknesses: [
      "Compliance scores not validated by a clinical expert — algorithmic basis opaque",
      "No benchmarking against existing tools (Veeva Vault, IQVIA, manual templates)",
      "RAG without real organizational data has no institutional memory yet",
    ],
    improvement:
      "Document the GCP/ICH and РФ НМД scoring formula in PROMPTS.md and get explicit sign-off from a Senior Clinical Research Analyst. Unvalidated regulatory scores are a liability in a GCP audit.",
  },
  {
    id: "quality",
    label: "Quality",
    score: 8.0,
    tone: "success" as const,
    justification:
      "137 passing tests (0 failed), comprehensive documentation suite, clean async architecture, unique fallback templates per section, test_new_features.py covers sessions 11–12. Significant improvement from 93→137 tests. CI/CD still manual.",
    strengths: [
      "137 automated tests (0 failed): unit, integration, smoke, RBAC, governance, fallbacks, phase IV",
      "test_new_features.py: edit metadata, exclusion criteria, SAP/ICF fallback uniqueness, export audit",
      "Unique fallback for every section including SAP/ICF — no copy-paste placeholders",
      "Rich documentation: test-plan v3.4.0, debug guide, manual test guide, API spec v1.6",
      "Clean async FastAPI + SQLAlchemy 2 — correct patterns throughout",
      "Export audit log (action='export') written on every export call",
    ],
    weaknesses: [
      "import pytest_asyncio on line 432 in test_new_features.py (should be at top)",
      "Gap: export→audit_log test declared in docstring but not written",
      "GitLab CI/CD non-functional (manual deploy only) — no regression guard between sessions",
      "AI Gateway integration tests use mocks exclusively",
    ],
    improvement:
      "Set up a CI pipeline (GitLab CI or GitHub Actions) that runs pytest on every push. Without automated CI, no regression protection exists between sessions.",
  },
];

const overallScore = (
  CATEGORIES.reduce((s, c) => s + c.score, 0) / CATEGORIES.length
).toFixed(1);

export default function SynthiaReview() {
  return (
    <Stack gap={24}>
      <Stack gap={6}>
        <H1>System Review — Synthia AI Protocol Generator</H1>
        <Row gap={8} wrap>
          {[
            "System Architect",
            "Product Manager",
            "Business Owner",
            "Designer",
            "Developer",
            "QA Engineer",
            "Analyst",
            "Clinical Research Analyst",
          ].map((role) => (
            <Pill key={role} size="sm" tone="neutral">
              {role}
            </Pill>
          ))}
        </Row>
      <Text tone="secondary" size="small">
        Evaluation date: 2026-04-24 · Project phase: MVP v1.2.0 · CHECKPOINT v12.0.0 · 137 tests
      </Text>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value="7.5" label="Total Value" tone="success" />
        <Stat value="7.0" label="Style" tone="info" />
        <Stat value="7.5" label="Innovation" tone="success" />
        <Stat value="8.0" label="Quality" tone="success" />
      </Grid>

      <BarChart
        categories={CATEGORIES.map((c) => c.label)}
        series={[{ name: "Score (out of 10)", data: CATEGORIES.map((c) => c.score) }]}
        horizontal
        height={140}
        valueSuffix="/10"
      />

      <Divider />

      <H2>Category Breakdown</H2>

      {CATEGORIES.map((cat) => (
        <Card key={cat.id} collapsible defaultOpen>
          <CardHeader trailing={<Pill tone={cat.tone} size="sm" active>{cat.score}/10</Pill>}>
            {cat.label}
          </CardHeader>
          <CardBody>
            <Stack gap={16}>
              <Text tone="secondary">{cat.justification}</Text>

              <Grid columns={2} gap={16}>
                <Stack gap={8}>
                  <H3>Strengths</H3>
                  <Stack gap={4}>
                    {cat.strengths.map((s, i) => (
                      <Text key={i} size="small">+ {s}</Text>
                    ))}
                  </Stack>
                </Stack>
                <Stack gap={8}>
                  <H3>Weaknesses</H3>
                  <Stack gap={4}>
                    {cat.weaknesses.map((w, i) => (
                      <Text key={i} size="small" tone="secondary">- {w}</Text>
                    ))}
                  </Stack>
                </Stack>
              </Grid>

              <Callout tone="neutral" title="One concrete improvement">
                {cat.improvement}
              </Callout>
            </Stack>
          </CardBody>
        </Card>
      ))}

      <Divider />

      <H2>Summary Table</H2>
      <Table
        headers={["Category", "Score", "Key Strength", "Key Risk"]}
        rows={[
          ["Total Value", "7.5/10", "SAP/ICF + Governance + Open Issues export", "AI Gateway needs BIOCAD network"],
          ["Style", "7.0/10", "CreateProtocolPage + AutocompleteField + Diff viewer", "No mobile layout, no loading skeletons"],
          ["Innovation", "7.5/10", "Internal-only LLM, SAP/ICF generation, RAG Phase 1", "Scores unvalidated by clinical expert"],
          ["Quality", "8.0/10", "137 tests (0 failed), test_new_features.py, unique fallbacks", "CI/CD manual only, import order bug"],
        ]}
        columnAlign={["left", "center", "left", "left"]}
        rowTone={[undefined, undefined, "success", "success"]}
        striped
      />

      <Divider />

      <H2>Verdict</H2>

      <Grid columns={3} gap={12}>
        <Stat value={overallScore} label="Overall Score" tone="info" />
        <Stat value="CONTINUE" label="Recommendation" tone="success" />
        <Stat value="P0" label="Priority Fix" tone="warning" />
      </Grid>

      <Callout tone="success" title="Overall verdict: Production-ready after one security fix">
        Synthia v1.2.0 is a technically sound, domain-relevant system with a clear value proposition for
        BIOCAD clinical research workflows. The architecture is clean (async FastAPI + SQLAlchemy 2),
        the documentation thorough (test plan v3.4.0, debug guide, API spec v1.6), and the 137-test
        suite (0 failures) provides solid regression coverage. SAP/ICF generation and governance
        workflow exceed the original MVP scope.
      </Callout>

      <Stack gap={12}>
        <H3>Short summary</H3>
        <Text>
          The system successfully addresses a real and costly problem — manual GCP-compliant
          protocol authorship — with an AI-first approach that is architecturally sound and
          compliant with internal data governance requirements. Three gaps must be closed
          before production delivery:
        </Text>
        <Stack gap={6}>
          <Text size="small" weight="semibold">P0 — Before delivery</Text>
          <Text size="small">1. Rotate secret token from corecase.md immediately — plain-text third-party API key in repository is a critical security risk.</Text>
          <Text size="small">2. Dokploy redeploy after migrations 004–005. Run alembic upgrade head on production DB.</Text>
          <Text size="small">3. Compliance scores (GCP/ICH + РФ НМД) require sign-off from a Senior Clinical Research Analyst before stakeholder demo.</Text>

          <Text size="small" weight="semibold">P1 — Within first sprint after delivery</Text>
          <Text size="small">4. CI/CD pipeline (GitLab CI / GitHub Actions) that runs pytest on every push. Currently no regression guard.</Text>
          <Text size="small">5. Fix import order in test_new_features.py (pytest_asyncio at line 432, needs to be at top).</Text>
          <Text size="small">6. Create .env.example template (README references it, file doesn't exist).</Text>

          <Text size="small" weight="semibold">P2 — Backlog</Text>
          <Text size="small">7. RAG pgvector extension. Phase 1 (JSONB) is ready; Phase 2 (pgvector similarity) is the next major value unlock.</Text>
          <Text size="small">8. ct.biocad.ru integration (deferred post-MVP). Will close the data-import loop.</Text>
        </Stack>
      </Stack>

      <Text tone="tertiary" size="small">
        Review generated by Synthia project AI agent · All scores are cross-role composite assessments
      </Text>
    </Stack>
  );
}
