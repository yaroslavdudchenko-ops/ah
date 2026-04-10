---
name: k8s-deploy-scaffold
description: >-
  Scaffold Kubernetes deployment for GitLab projects: generates Helm charts
  (bcd-web), .gitlab-ci.yml, docker-compose.yaml, Dockerfiles directly in the
  repo, plus a DEPLOYMENT.md file with Vault templates, Argo CD manifests,
  PowerDNS records, and a review checklist. Use when creating helm/,
  .gitlab-ci.yml, docker-compose, Dockerfile, or when the user says "deploy",
  "release", "pipeline", "scaffold", "infra" — even without mentioning Helm
  explicitly.
---

# Kubernetes Deployment Scaffold

Analyze a project repository and generate deployment files: Helm charts, GitLab CI pipeline, docker-compose, Dockerfiles, Vault secret templates. All recommendations and advisory content (Argo CD infrastructure, PowerDNS records, Vault templates, review checklist) are written to a single `DEPLOYMENT.md` file in the repository root — the engineer reads it, configures everything, and decides whether to keep it as documentation or delete it.

## Workflow

1. **Analyze** the repository: source code, existing Dockerfiles, docker-compose, environment variables, dependencies, exposed ports, health endpoints
2. **Generate** deployment files in the project repository: `helm/`, `.gitlab-ci.yml`, `docker-compose.yaml`, Dockerfiles (if missing)
3. **Write `DEPLOYMENT.md`** in the repo root — a single file containing:
   - Vault secret templates per service
   - Argo CD file recommendations for the argocd-infra repository (namespace, dependencies, ingress, ExternalSecrets)
   - PowerDNS records if Ingress is needed
   - Review summary table with all `# REVIEW:` fields

Generated code files (`helm/`, `.gitlab-ci.yml`, `docker-compose.yaml`, Dockerfiles) are created directly in the repository. Everything else goes into `DEPLOYMENT.md`.

### Uncertain Values — `# REVIEW:` Marker

Many values cannot be determined from the repository alone. Mark every such value with an inline comment `# REVIEW: <reason>` so the user can find and adjust them.

**What to mark:** runner tags, CI component version, Argo CD project (`dis`/`dcm`/`dir`/`dib`/`dot`), namespace name, environment name, Ingress host (`*.biocad.dev`) and CNAME target, wildcard TLS Secret name, resource limits/requests, ResourceQuota values, whitelist CIDRs, DB user/name, Vault path (cluster prefix in ExternalSecrets), health endpoint path.

**How to mark** — append `# REVIEW:` to the line:

```yaml
  tags:
    - rancher-kube-prod              # REVIEW: verify runner tag for target cluster
spec:
  project: dis                       # REVIEW: set correct Argo CD project (dis/dcm/dir/dib/dot)
  destination:
    namespace: dis-voiceai-dev       # REVIEW: adjust namespace to match your project and environment
```

When a value **can** be determined from the repository (e.g. port from `EXPOSE`, env var name from code), do not mark it — only mark what requires human decision.

### Review Summary

After generating all files, write a **"Review Required"** section at the end of `DEPLOYMENT.md` — a table listing every `# REVIEW:` field, grouped by file, with the current best-guess value and what the engineer needs to check. This lets the engineer address all uncertain values in one pass without searching through configs.

---

## Step 1 — Repository Analysis

Scan the repository for:

- **Services**: directories with Dockerfiles, `main.go`, `app.py`, `package.json`, `pom.xml`, etc.
- **Existing Dockerfiles**: evaluate quality, suggest improvements or create missing ones
- **docker-compose.yaml**: existing or absent — generate either way. Use [references/compose-mapping.md](references/compose-mapping.md) to translate each compose construct to bcd-web values, Vault, and Argo CD
- **Environment variables**: from `.env.example`, docker-compose, code (`os.getenv`, `process.env`, `os.Getenv`, `System.getenv`)
- **Exposed ports**: from Dockerfiles (`EXPOSE`), code (listen calls), docker-compose
- **Health endpoints**: `/health`, `/healthz`, `/ready`, `/api/health`
- **Infrastructure dependencies**: databases, caches, brokers (see trigger keywords below)
- **Persistent storage needs**: file uploads, data directories

Classify every discovered variable as:
- **Config** (non-sensitive) → goes to `configmaps_create` in values.yaml and `environment` in docker-compose
- **Secret** (API keys, passwords, tokens, connection strings with credentials) → goes to Vault template and docker-compose `.env` reference

---

## Step 2 — Generate Project Files

### 2.1 Dockerfiles

If the repository lacks Dockerfiles, or has suboptimal ones, generate production-ready Dockerfiles per service.

**Requirements:**
- Multi-stage builds (build + runtime)
- Non-root user (UID/GID 1000) — bcd-web enforces `runAsUser: 1000`, `runAsGroup: 1000`
- Minimal base images (`alpine`, `distroless`, `slim`)
- `EXPOSE` with the actual port
- `HEALTHCHECK` instruction
- `.dockerignore` in same directory

For Dockerfile templates per language (Go, Python, Node.js, Java, .NET), see [references/dockerfiles.md](references/dockerfiles.md).

### 2.2 docker-compose.yaml

Generate a production-representative docker-compose for local development that mirrors the Kubernetes deployment.

**Requirements:**
- All project services with correct build contexts and Dockerfiles
- All infrastructure dependencies (postgres, redis, etc.) with pinned image versions
- Environment variables split: non-secret inline, secrets via `env_file: .env`
- Port mappings matching Helm values
- Health checks matching probe configuration
- Volume mounts for persistent data
- `depends_on` with `condition: service_healthy` for dependency ordering
- Network isolation between unrelated services

Also generate `.env.example` with all secret variables (empty values) alongside docker-compose.

For docker-compose templates (application services, PostgreSQL, Redis, RabbitMQ, MongoDB, MinIO, Kafka), see [references/docker-compose.md](references/docker-compose.md).

### 2.3 Helm Charts

For each application service, generate `helm/{service}/Chart.yaml` and `helm/{service}/values.yaml`.

No `templates/` directory — all templates come from the `bcd-web` dependency chart.

**Chart.yaml:**

```yaml
apiVersion: v2
name: {project}-{service}
description: A Helm chart for {Service Description}
type: application
version: 0.0.1
appVersion: "no"

dependencies:
  - name: bcd-web
    version: 0.2.1
    repository: "https://charts.k8s.biocad.ru/"
```

**values.yaml** — fill from analysis results. For full bcd-web values reference, see [references/bcd-web-values.md](references/bcd-web-values.md).

```yaml
bcd-web:
  annotations:
    reloader.stakater.com/auto: "true"

  containers:
    {service}:
      image:
        repository: $CI_REGISTRY_IMAGE
        tag: ${CI_COMMIT_TAG:-$CI_COMMIT_SHORT_SHA}
        suffix: {service}
        pullPolicy: IfNotPresent
      ports:
        - containerPort: {port}
          name: {port-name}
          protocol: TCP
      securityContext:
        runAsUser: 1000
        runAsGroup: 1000
        readOnlyRootFilesystem: false
      envFromSecrets:
        - {project}-{service}-sec
      envFromConfigMaps:
        - {project}-{service}-config
      livenessProbe:
        enabled: true
        probe:
          httpGet:
            path: /health
            port: {port-name}
          initialDelaySeconds: 10
          periodSeconds: 15
          failureThreshold: 3
          timeoutSeconds: 5
      readinessProbe:
        enabled: true
        probe:
          httpGet:
            path: /health
            port: {port-name}
          initialDelaySeconds: 10
          periodSeconds: 10
          failureThreshold: 3
          timeoutSeconds: 1
      resources:
        requests:
          cpu: 200m
          memory: 256Mi
        limits:
          cpu: 500m
          memory: 512Mi
      volumeMounts: []

  podSecurityContext:
    fsGroup: 1000

  configmaps_create:
    {project}-{service}-config:
      # all non-secret env vars discovered during analysis
      KEY: "value"

  volumes: []

  persistence: {}

  affinity: {}

  service:
    {service}:
      ports:
        - port: {external-port}
          targetPort: {port-name}
          protocol: TCP
          name: {port-name}

  networkPolicy:
    enabled: true
    policyTypes:
      - Ingress
    ingress:
      - from:
          - ipBlock:
              cidr: 10.0.0.0/8
        ports:
          - protocol: TCP
            port: {port}

  imagePullSecrets:
    - name: {project}-regcred

  fullnameOverride: "{project}-{service}"
```

### 2.4 GitLab CI Pipeline (.gitlab-ci.yml)

```yaml
include:
  - component: gitlab.biocad.ru/iac/ci-components/main/ci@1.5.12
  - component: gitlab.biocad.ru/iac/ci-components/ci/bumpversion/date@~latest
    inputs:
      trigger_mode: "on_success"

stages:
  - bumpversion
  - build
  - deploy

.protected_tag_rules:
  rules:
    - if: $CI_COMMIT_REF_PROTECTED == "true" && $CI_COMMIT_TAG

build:services:
  stage: build
  extends: .image.Matrix-Build
  rules:
    - !reference [.protected_tag_rules, rules]
  parallel:
    matrix:
      # one entry per service discovered during analysis
      - BUILD_PATH: "{service-dir}"
        BUILD_FILE: "Dockerfile"
        IMAGE_SUFFIX: "{service}"

.deploy_template:
  stage: deploy
  extends: .k8s.Helm.Install
  variables:
    HELM_VALUES_SECRET: "values-secret.tmp.yaml"
  before_script:
    - cat $helm_values > values-secret.tmp.yaml

# one .deploy_{service} per service
.deploy_{service}:
  extends: .deploy_template
  variables:
    HELM_RELEASE: "{project}-{service}"
    HELM_CHART: "helm/{service}"
    HELM_VALUES: "helm/{service}/values.yaml"
  secrets:
    helm_values:
      vault: "dir/${CI_PROJECT_NAME}/${CI_PROJECT_ID}/${CI_COMMIT_REF_PROTECTED}/${CI_ENVIRONMENT_NAME}/helm_values_{service}@gitlab-kv"
      file: true

# environment anchors
.deploy_prod: &deploy_prod_template
  environment:
    name: "{argo-project}-{project}-prod"
  rules:
    - !reference [.protected_tag_rules, rules]
  tags:
    - rancher-kube-prod

# final deploy jobs
deploy:{service}:prod:
  extends: .deploy_{service}
  <<: *deploy_prod_template
```

### 2.5 Vault Secret Templates

After generating Helm charts, write a **"Vault Secrets"** section into `DEPLOYMENT.md` with a template per service:

````markdown
## Vault Secrets

### {service}

**Path:** `dir/{CI_PROJECT_NAME}/{CI_PROJECT_ID}/{CI_COMMIT_REF_PROTECTED}/{CI_ENVIRONMENT_NAME}/helm_values_{service}@gitlab-kv`

```yaml
bcd-web:
  containers:
    {service}:
      envFromSecrets:
        - {project}-{service}-sec

  secrets_create:
    {project}-{service}-sec:
      SECRET_VAR_1: ""
      SECRET_VAR_2: ""
```
````

List **every** secret variable discovered during analysis. Leave values empty — the user fills them.

---

## Step 3 — Argo CD Recommendations

Write an **"Argo CD"** section into `DEPLOYMENT.md` with ready-to-use YAML files that the engineer commits to the appropriate `argocd-infra-*` repository for their target cluster. Each cluster has its own repository with identical directory structure (`dis/`, `dcm/`, `dir/`, `dib/`, `dot/`). Do not create these files in the project repository.

Mark all cluster-dependent values (`# REVIEW:`): Argo CD project, namespace, `repoURL`, `storageClass`, Ingress host, Vault paths in ExternalSecrets (cluster prefix differs).

For detailed reference on Argo CD patterns, see [references/argocd-infra.md](references/argocd-infra.md).

### 3.1 Namespace (ns-hr.yaml)

Write a subsection `### Namespace (ns-hr.yaml)` into the Argo CD section of `DEPLOYMENT.md`. Include the full YAML for `{argo-project}/{project}-{env}/ns-hr.yaml` using the `k8s-ns` chart (`~1.2.2`), with `developers`, `resourceQuota`, `limitRange` values sized for the project. Use `CreateNamespace=true` in syncOptions. Mark `project`, namespace, quota values with `# REVIEW:`.

For the full template and quota sizing guide, see [references/argocd-infra.md](references/argocd-infra.md) (Namespace Application). For k8s-ns chart values, see [references/ns-chart-values.md](references/ns-chart-values.md).

### 3.2 Registry Credentials (regcred-es.yaml)

Write a subsection `### Registry Credentials (regcred-es.yaml)` with the full ExternalSecret YAML — syncs registry credentials from Vault via `ClusterSecretStore` `vault-css` into a `kubernetes.io/dockerconfigjson` Secret named `regcred`. Mark the Vault path with `# REVIEW:` — the cluster prefix differs per target.

For the template, see [references/argocd-infra.md](references/argocd-infra.md) (External Secrets).

### 3.3 Infrastructure Dependencies

When analysis detects stateful infrastructure, recommend Argo CD Application manifests with `sync-wave: "1"`.

**Trigger keywords:**

| Component | Triggers in docker-compose / code / docs |
|---|---|
| PostgreSQL | `postgres`, `pgbouncer`, `POSTGRES_`, `DATABASE_URL` |
| Redis | `redis`, `REDIS_URL`, `REDIS_HOST` |
| RabbitMQ | `rabbitmq`, `AMQP_URL`, `RABBITMQ_` |
| Kafka | `kafka`, `KAFKA_BOOTSTRAP_SERVERS` |
| MongoDB | `mongo`, `MONGO_URL`, `MONGODB_URI` |
| Elasticsearch | `elasticsearch`, `ELASTIC_` |
| MinIO | `minio`, `S3_ENDPOINT`, `AWS_S3_` |
| MySQL | `mysql`, `mariadb`, `MYSQL_` |

For each detected dependency, write into `DEPLOYMENT.md`:
1. Application YAML `{argo-project}/{project}-{env}/{component}.yaml` — mark `repoURL`, `storageClass`, resource sizes with `# REVIEW:`
2. ExternalSecret YAML `{argo-project}/{project}-{env}/{component}-secret-es.yaml` — syncs credentials from Vault, mark path with `# REVIEW:`
3. A note reminding the engineer to create corresponding Vault entries at the expected paths

For full templates, see [references/argocd-infra.md](references/argocd-infra.md) (Infrastructure Components, External Secrets).

### 3.4 Ingress (ingress.yaml)

If the project has externally accessible services, write a subsection `### Ingress (ingress.yaml)` with the full raw Ingress manifest — nginx annotations, `sync-wave: "1"`. Hosts use **3rd-level domains** under `biocad.dev` (e.g. `{project}.biocad.dev`). TLS is provided by a purchased wildcard certificate — do not use cert-manager annotations. Mark the host and wildcard TLS Secret name with `# REVIEW:`.

For the full template, see [references/argocd-infra.md](references/argocd-infra.md) (Ingress Manifests).

---

## Step 4 — PowerDNS Record

If Ingress is recommended, write a **"PowerDNS"** section into `DEPLOYMENT.md`:

````markdown
## PowerDNS

Add a CNAME record via the PowerDNS Terraform repository. The record points the Ingress host to the GSLB zone of the target cluster.

| Type | Name | Content | TTL |
|---|---|---|---|
| CNAME | `{project}.biocad.dev` | `{cluster-gslb}.gslb.biocad.ru.` | 300 | <!-- REVIEW: GSLB zone name for target cluster -->

GSLB zones are named after the cluster (e.g. `rancher-kube-dev.gslb.biocad.ru.`, `rancher-kube-dr.gslb.biocad.ru.`), but the exact name may differ — verify with the platform team or check existing records in the PowerDNS Terraform repo for the pattern used in your environment.

Without this record, the Ingress will be configured but the host won't be resolvable from the network.
````

---

## Naming Conventions

| Entity | Pattern | Example |
|---|---|---|
| Helm release | `{project}-{service}` | `voiceai-orchestrator` |
| Namespace | `{argo-project}-{project}-{env}` | `dis-voiceai-prod` |
| Chart dir | `helm/{service}/` | `helm/orchestrator/` |
| Image suffix | service name | `orchestrator` |
| ConfigMap | `{project}-{service}-config` | `voiceai-orchestrator-config` |
| Secret (Vault) | `{project}-{service}-sec` | `voiceai-orchestrator-sec` |
| fullnameOverride | `{project}-{service}` | `voiceai-orchestrator` |
| imagePullSecret | `{project}-regcred` | `voiceai-regcred` |
| Argo CD App (ns) | `{argo-project}-{project}-{env}` | `dis-voiceai-dev` |
| Argo CD App (infra) | `{project}-{component}` | `voiceai-postgresql` |
| Ingress host | `{project}.biocad.dev` | `voiceai.biocad.dev` |
| PowerDNS CNAME | `{project}.biocad.dev` → `{cluster-gslb}.gslb.biocad.ru.` | `voiceai.biocad.dev` → `rancher-kube-dev.gslb.biocad.ru.` |

Labels (set by bcd-web `_helpers.tpl`):

```yaml
app.kubernetes.io/name: bcd-web
app.kubernetes.io/instance: {HELM_RELEASE}
```

### Image Tag Strategy

```yaml
image:
  repository: $CI_REGISTRY_IMAGE
  tag: ${CI_COMMIT_TAG:-$CI_COMMIT_SHORT_SHA}
  suffix: {service}
```

### Secrets

Never in values.yaml. Vault path:

```
dir/{CI_PROJECT_NAME}/{CI_PROJECT_ID}/{CI_COMMIT_REF_PROTECTED}/{CI_ENVIRONMENT_NAME}/helm_values_{service}@gitlab-kv
```

---

## Shared ReadWriteOnce Volumes

When two or more services mount the **same PVC** with `ReadWriteOnce`:

1. **Owner** — the service that creates the PVC via `persistence`. No affinity constraint, schedules freely.
2. **Dependents** — add `podAffinity` to the owner:

```yaml
  affinity:
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchLabels:
              app.kubernetes.io/name: bcd-web
              app.kubernetes.io/instance: {project}-{owner-service}
          topologyKey: kubernetes.io/hostname
```

3. Never set mutual affinity (deadlock).
4. Dependents reference PVC by name in `volumes`, do not duplicate in `persistence`.

---

## Output Checklist

When the skill completes, the repository should contain:

### Generated Files (in project repository)

- [ ] Dockerfiles per service (if missing or improved)
- [ ] `.dockerignore` per service
- [ ] `docker-compose.yaml` with all services and infrastructure
- [ ] `.env.example` with all secret variables (empty)
- [ ] `helm/{service}/Chart.yaml` per service (bcd-web 0.2.1)
- [ ] `helm/{service}/values.yaml` per service (all env vars classified)
- [ ] `.gitlab-ci.yml` with build matrix and deploy jobs

### `DEPLOYMENT.md` (in project repository root)

Single file the engineer reads through, configures, and later keeps or deletes:

- [ ] **Vault Secrets** — template per service with path and YAML
- [ ] **Argo CD** — `ns-hr.yaml` (namespace, k8s-ns ~1.2.2)
- [ ] **Argo CD** — `regcred-es.yaml` (ExternalSecret for registry credentials)
- [ ] **Argo CD** — infrastructure component Applications with `sync-wave: "1"` (per detected dependency)
- [ ] **Argo CD** — ExternalSecret manifests per component (Vault-backed via `vault-css`)
- [ ] **Argo CD** — `ingress.yaml` (if external access needed)
- [ ] **PowerDNS** — DNS record table for each Ingress host
- [ ] **Review Required** — summary table of all `# REVIEW:` fields across all files

## Additional Resources

- For bcd-web chart values reference, see [references/bcd-web-values.md](references/bcd-web-values.md)
- For ns-chart (k8s-ns) values reference, see [references/ns-chart-values.md](references/ns-chart-values.md)
- For Argo CD infrastructure patterns, see [references/argocd-infra.md](references/argocd-infra.md)
- For Docker Compose → bcd-web mapping table, see [references/compose-mapping.md](references/compose-mapping.md)
