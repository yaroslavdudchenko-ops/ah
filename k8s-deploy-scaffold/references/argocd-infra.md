# Argo CD Infrastructure Patterns Reference

Use this reference when generating Argo CD Application manifests. These patterns are **cluster-agnostic** — the same structure, projects, and conventions apply to every `argocd-infra-*` repository regardless of which Kubernetes cluster it targets.

## Table of Contents

- [Multi-Cluster Model](#multi-cluster-model)
- [Repository Architecture](#repository-architecture)
- [App-of-Apps Pattern](#app-of-apps-pattern)
- [Namespace Application](#namespace-application)
- [Infrastructure Components](#infrastructure-components)
- [External Secrets (ESO)](#external-secrets-eso)
- [Ingress Manifests](#ingress-manifests)
- [Sync Policies and Ordering](#sync-policies-and-ordering)
- [Environment Folder Checklist](#environment-folder-checklist)

## Multi-Cluster Model

Each Kubernetes cluster has its own dedicated argocd-infra repository:

```
argocd-infra-dev    → dev cluster
argocd-infra-prod   → prod cluster
argocd-infra-dr     → disaster recovery cluster
argocd-infra-stage  → staging cluster
...
```

All repositories share the **identical directory structure** — the same Argo CD projects (`dis`, `dcm`, `dir`, `dib`, `dot`, `cluster`), the same app-of-apps pattern, the same file naming conventions. The only differences between repositories are:

- Helm values (resource sizes, replica counts, persistence settings)
- Ingress hosts (cluster-specific 3rd-level domains under `*.biocad.dev`)
- Vault paths in ExternalSecrets (cluster name prefix differs)
- Chart versions may vary during rollout across clusters

When generating Argo CD recommendations, do not hardcode a specific cluster name. Use `# REVIEW: target argocd-infra repository for your cluster` so the user places files in the correct repository.

## Repository Architecture

```
argocd-infra-{cluster}/                  # REVIEW: one repo per cluster
├── cluster/                             # platform-level (argocd, monitoring, ingress, etc.)
│   └── argocd/
│       ├── argocd-apps-app.yaml         # app-of-apps + AppProject definitions
│       └── argocd-hr.yaml               # argocd server
├── dis/{project}-{env}/                 # REVIEW: argo-project depends on team
├── dcm/{project}-{env}/
├── dir/{project}-{env}/
├── dib/{project}-{env}/
└── dot/{project}-{env}/
```

Top-level directories correspond to **Argo CD projects** (organizational units). Each is synced **recursively** by a parent Application — every YAML file placed inside is automatically applied to the cluster.

### Argo CD Projects

| Project | Scope |
|---|---|
| `cluster` | Platform infrastructure (monitoring, ingress, storage, security) |
| `dis` | Product team environments |
| `dcm` | DCM team environments |
| `dir` | Internal tools and shared services |
| `dib` | DIB team environments |
| `dot` | DOT team environments |

The project list is identical across all cluster repositories. All projects share permissive settings: `sourceRepos: ['*']`, `destinations: namespace '*'`, `clusterResourceWhitelist: '*/*'`, `orphanedResources.warn: true`.

The skill cannot determine which project a repository belongs to — mark with `# REVIEW: set correct Argo CD project (dis/dcm/dir/dib/dot)`.

## App-of-Apps Pattern

The hub is `cluster/argocd/argocd-apps-app.yaml` — an `Application` that installs the `argocd-apps` Helm chart, which defines:

1. **Child Applications** — one per top-level directory, each with `directory.recurse: true`
2. **AppProjects** — one per organizational unit

Child Applications use `prune: false, selfHeal: false` — the umbrella tracks but does not auto-prune leaf manifests. Leaf Applications within each folder define their own sync policies (typically `prune: true, selfHeal: true`).

## Namespace Application

Every environment folder starts with a namespace Application using the `k8s-ns` chart.

### Naming

- **Application name:** `{argo-project}-{project}-{env}` (e.g. `dis-parcur-dev`)
- **Destination namespace:** same as application name
- **File name:** `ns-hr.yaml` (or `ns-app.yaml`)

### Template

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {argo-project}-{project}-{env}       # REVIEW: argo-project (dis/dcm/dir/dib/dot), project name, env
  namespace: argocd
spec:
  project: {argo-project}                     # REVIEW: set correct Argo CD project
  source:
    chart: k8s-ns
    repoURL: "https://charts.k8s.biocad.ru/"
    targetRevision: ~1.2.2
    helm:
      values: |
        rbacPrefix: "oidc:"
        developers:
          - {username}                        # REVIEW: developer usernames for RBAC
        networkPolicy:
          enabled: false
        limitRange:
          - default:
              cpu: 750m
              memory: 1Gi
            defaultRequest:
              cpu: 500m
              memory: 512Mi
            type: Container
        resourceQuota:
          hard:
            limits.cpu: "16"                  # REVIEW: adjust to team resource budget
            limits.memory: 24Gi               # REVIEW: adjust to team resource budget
            persistentvolumeclaims: "5"
            pods: "10"                        # REVIEW: expected pod count
            requests.cpu: "10"
            requests.memory: 16Gi
            requests.storage: 50Gi
  destination:
    server: https://kubernetes.default.svc
    namespace: {argo-project}-{project}-{env} # REVIEW: must match metadata.name
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### Resource Quota Sizing Guide

| Profile | limits.cpu | limits.memory | pods | requests.storage |
|---|---|---|---|---|
| Small (dev/test) | "4" | 8Gi | "5" | 10Gi |
| Medium | "10"-"16" | 16Gi-24Gi | "10" | 50Gi |
| Large (prod) | "32"+ | 64Gi+ | "20"+ | 100Gi+ |

## Infrastructure Components

All components follow the same Application structure with `sync-wave: "1"` to deploy after the namespace.

### PostgreSQL

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {project}-postgresql                  # REVIEW: project name
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "1"
spec:
  project: {argo-project}                     # REVIEW: Argo CD project
  source:
    chart: postgresql
    repoURL: "docker.biocad.ru/bitnamicharts" # REVIEW: may differ per cluster (see alternatives below)
    targetRevision: 12.12.10                  # REVIEW: chart version
    helm:
      values: |
        image:
          registry: docker.biocad.ru
          repository: bitnamilegacy/postgresql
          tag: 15.4.0-debian-11-r45           # REVIEW: PostgreSQL version
          pullPolicy: IfNotPresent
        fullnameOverride: "{project}-postgres" # REVIEW: project name
        global:
          postgresql:
            auth:
              username: "{db-user}"           # REVIEW: database username
              database: "{db-name}"           # REVIEW: database name
              existingSecret: "postgres-secret"
        postgresqlSharedPreloadLibraries: "pgaudit,pg_stat_statements"
        primary:
          resources:
            limits:
              memory: 4Gi                     # REVIEW: resource sizing
              cpu: 2
            requests:
              memory: 1Gi
              cpu: 1
          persistence:
            enabled: true
            storageClass: ""                  # REVIEW: may need explicit storageClass per cluster
            accessModes:
              - ReadWriteOnce
            size: 5Gi                         # REVIEW: disk size
        metrics:
          enabled: true
          serviceMonitor:
            enabled: true
          prometheusRule:
            enabled: true
            namespace: "monitoring"
  destination:
    server: https://kubernetes.default.svc
    namespace: {argo-project}-{project}-{env} # REVIEW: namespace
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

Alternative `repoURL` values (varies per cluster network access):
- `docker.biocad.ru/bitnamicharts` — internal mirror
- `https://charts.bitnami.com/bitnami/` — public Bitnami
- `registry-1.docker.io/bitnamicharts` — Docker Hub OCI

Credentials go in an ExternalSecret named `postgres-secret-es` that syncs from Vault into a Secret named `postgres-secret`. See [External Secrets (ESO)](#external-secrets-eso) section.

### Redis

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {project}-redis                       # REVIEW: project name
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "1"
spec:
  project: {argo-project}                     # REVIEW: Argo CD project
  source:
    chart: redis
    repoURL: "https://charts.bitnami.com/bitnami/" # REVIEW: may use internal mirror
    targetRevision: 17.1.2                    # REVIEW: chart version
    helm:
      values: |
        architecture: standalone
        auth:
          enabled: false
          sentinel: false
        master:
          persistence:
            enabled: true
            storageClass: ""                  # REVIEW: may need explicit storageClass per cluster
            path: /data
            accessModes:
              - ReadWriteOnce
            size: 10Gi                        # REVIEW: disk size
          service:
            type: ClusterIP
            port: 6379
            portName: redis
        replica:
          replicaCount: 0
          persistence:
            enabled: false
  destination:
    server: https://kubernetes.default.svc
    namespace: {argo-project}-{project}-{env} # REVIEW: namespace
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

For dev/test without persistence:

```yaml
        master:
          persistence:
            enabled: false
        replica:
          replicaCount: 0
          persistence:
            enabled: false
```

### Chart Reference Table

| Component | Chart | repoURL | Typical targetRevision |
|---|---|---|---|
| PostgreSQL | `postgresql` | `docker.biocad.ru/bitnamicharts` | `12.12.10` |
| Redis | `redis` | `https://charts.bitnami.com/bitnami/` | `17.1.2` |
| RabbitMQ | `rabbitmq` | `https://charts.bitnami.com/bitnami/` | latest stable |
| MongoDB | `mongodb` | `https://charts.bitnami.com/bitnami/` | latest stable |
| MySQL | `mysql` | `https://charts.bitnami.com/bitnami/` | latest stable |
| MinIO | `minio` | `https://charts.bitnami.com/bitnami/` | latest stable |
| Kafka | `kafka` | `https://charts.bitnami.com/bitnami/` | latest stable |

All `repoURL` values may differ per cluster — internal clusters may use `docker.biocad.ru/bitnamicharts`, clusters with public access may use `https://charts.bitnami.com/bitnami/`. Mark with `# REVIEW:` when generating.

## External Secrets (ESO)

Secrets are managed via **External Secrets Operator** (ESO) with HashiCorp Vault as the backend. ExternalSecret manifests are placed alongside Application manifests in the environment folder — the recursive directory sync picks them up automatically.

All clusters use a shared `ClusterSecretStore` named `vault-css` that connects to Vault.

### Vault Path Convention

```
{cluster}/{argo-project}/{namespace}/{secret-name}
```

Examples:
- `k8s-prod/dir/dir-voiceai-prod/regcred`
- `k8s-dev/dis/dis-parcur-dev/postgres-secret`

The `{cluster}` prefix matches the target cluster name (`k8s-prod`, `k8s-dev`, etc.). Mark with `# REVIEW:` — the skill cannot determine which cluster the deployment targets.

### Registry Credentials (regcred)

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: {project}-regcred-es
  namespace: {argo-project}-{project}-{env}          # REVIEW: namespace
spec:
  refreshInterval: 1m
  secretStoreRef:
    name: vault-css
    kind: ClusterSecretStore
  target:
    name: regcred
    template:
      type: kubernetes.io/dockerconfigjson
  dataFrom:
    - extract:
        key: {cluster}/{argo-project}/{argo-project}-{project}-{env}/regcred  # REVIEW: cluster prefix and full path
```

### Component Credentials (e.g. PostgreSQL)

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: {project}-postgres-secret-es
  namespace: {argo-project}-{project}-{env}          # REVIEW: namespace
spec:
  refreshInterval: 1m0s
  secretStoreRef:
    name: vault-css
    kind: ClusterSecretStore
  target:
    name: postgres-secret
  dataFrom:
    - extract:
        key: {cluster}/{argo-project}/{argo-project}-{project}-{env}/postgres-secret  # REVIEW: cluster prefix and full path
```

The `target.name` must match what the Helm chart references (e.g. `existingSecret: "postgres-secret"` in PostgreSQL Application values).

### Generic ExternalSecret Pattern

For any secret needed in the namespace:

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: {secret-name}-es
  namespace: {argo-project}-{project}-{env}          # REVIEW: namespace
spec:
  refreshInterval: 1m0s
  secretStoreRef:
    name: vault-css
    kind: ClusterSecretStore
  target:
    name: {secret-name}                              # K8s Secret name the workload expects
  dataFrom:
    - extract:
        key: {cluster}/{argo-project}/{namespace}/{secret-name}  # REVIEW: full Vault path
```

Use `target.template.type` only when a specific Secret type is required (e.g. `kubernetes.io/dockerconfigjson` for regcred). For generic Opaque secrets, omit `template`.

### Vault Secret Setup

After generating ExternalSecret manifests, remind the user to create the corresponding entries in Vault at the expected paths. The Vault data should contain key-value pairs matching what the application expects (e.g. `password`, `postgres-password` for PostgreSQL).

## Ingress Manifests

Placed as raw Kubernetes YAML (not Argo CD Applications) in the environment folder.

### Host Naming

All new hosts use **3rd-level domains** under `biocad.dev`:

```
{project}.biocad.dev
```

Not 4th-level (`{project}.kube-{env}.biocad.dev`). The 3rd-level format is the current standard.

### TLS

TLS is provided by a **purchased wildcard certificate** for `*.biocad.dev`, stored as a Kubernetes Secret (typically replicated across namespaces). Do not use `cert-manager.io/cluster-issuer` annotations — the wildcard cert covers all 3rd-level hosts.

### Template

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {project}
  namespace: {argo-project}-{project}-{env}   # REVIEW: namespace
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/whitelist-source-range: "10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16" # REVIEW: CIDRs per cluster
    nginx.ingress.kubernetes.io/proxy-body-size: 25m
    nginx.ingress.kubernetes.io/proxy-read-timeout: "600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "600"
    nginx.ingress.kubernetes.io/custom-http-errors: "503"
    argocd.argoproj.io/sync-wave: "1"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - {project}.biocad.dev                # REVIEW: 3rd-level domain under biocad.dev
      secretName: biocad-dev-wildcard-tls     # REVIEW: name of wildcard cert Secret in namespace
  rules:
    - host: {project}.biocad.dev              # REVIEW: must match tls[].hosts
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {service-name}
                port:
                  number: {port}
```

The wildcard TLS Secret name may vary per cluster — mark with `# REVIEW:`. If the Secret is not present in the namespace, it may need to be replicated (e.g. via kubernetes-replicator or an ExternalSecret from Vault).

## Sync Policies and Ordering

### Sync-Wave Strategy

| Wave | Resources |
|---|---|
| `0` (default) | Namespace Application (`ns-hr.yaml`) |
| `1` | Infrastructure components (postgres, redis, ingress, etc.) |

### Standard Sync Policy (leaf Applications)

```yaml
syncPolicy:
  automated:
    prune: true
    selfHeal: true
  syncOptions:
    - CreateNamespace=true    # only on namespace Application
```

### Parent/Child Sync Policy

Parent (app-of-apps) child Applications use `prune: false, selfHeal: false` to avoid cascading deletes when files are temporarily removed from git.

## Environment Folder Checklist

Minimal set of files for a new environment. Create in the correct argocd-infra repository for the target cluster:

```
{argo-project}/{project}-{env}/
├── ns-hr.yaml                          # namespace (k8s-ns chart) — REQUIRED
├── regcred-es.yaml                     # ExternalSecret for registry credentials — REQUIRED for private images
├── ingress.yaml                        # ingress manifest — if external access needed
├── postgres.yaml (or pg-hr.yaml)       # PostgreSQL Application — if database needed
├── postgres-secret-es.yaml             # ExternalSecret for postgres credentials
├── redis.yaml (or redis-hr.yaml)       # Redis Application — if cache needed
└── ... additional components
```

For multi-cluster deployments, create the same folder structure in each argocd-infra repository, adjusting:
- Vault paths in ExternalSecrets (cluster prefix differs: `k8s-prod/...` vs `k8s-dev/...`)
- Resource sizes (prod typically larger than dev)
- Ingress hosts (3rd-level `*.biocad.dev` domains, choose appropriate name)
- Chart `repoURL` (internal mirror vs public, depending on cluster network)
- `storageClass` (may differ per cluster storage backend)
- Wildcard TLS Secret name (may vary per cluster)

Commit to the appropriate `{argo-project}/` directory. The recursive directory sync handles the rest.
