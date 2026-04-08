---
name: biocad-production-deploy
description: >-
  Deploy applications to Biocad Kubernetes using bcd-web-chart Helm chart.
  Converts docker-compose configurations to Helm charts with GitLab CI/CD pipeline.
  Use when deploying to production, creating Helm charts from docker-compose,
  or setting up GitLab CI pipelines for Kubernetes deployments.
---

# Biocad Production Deploy

Announce at start: **"I'm using the biocad-production-deploy skill to implement this plan."**

## Overview

This skill converts docker-compose based applications to Helm chart deployments using the `bcd-web-chart` dependency chart from `https://charts.k8s.biocad.ru/`.

## Process

### Step 1: Load and Review Plan

1. Read the plan file provided by user
2. Review critically - identify any questions or concerns
3. **If concerns exist**: Raise them with your human partner before starting
4. **If no concerns**: Create TodoWrite checklist and proceed

### Step 2: Execute Batch

#### 2.1 Analyze Docker Compose

Inspect docker-compose files in the repository:
- Identify services, images, and tags
- Extract environment variables
- Note volume mounts and ports
- Identify resource requirements (CPU, memory limits)
- Check for secrets and config maps

#### 2.2 Check for Sensitive Data

**IMPORTANT**: Scan for sensitive data before proceeding.

Check for:
- `.env` files in the repository
- `env_file:` references in docker-compose
- Hardcoded credentials, API keys, tokens in environment variables
- Database connection strings with passwords
- Secret files or references

**Sensitive data indicators:**
- Variables containing: `PASSWORD`, `SECRET`, `TOKEN`, `API_KEY`, `CREDENTIAL`, `PRIVATE_KEY`
- Database URLs with embedded credentials
- Any base64-encoded values that might be secrets

**If sensitive data is found**, notify the user:

> ⚠️ **Sensitive Data Detected**
> 
> The following sensitive data was found:
> - [list items found]
> 
> **Action Required**: Please contact the DevOps/Platform Engineers team to add these secrets to **HashiCorp Vault** before deployment.
> 
> Once secrets are in Vault, update `values.yaml` to reference them via:
> ```yaml
> bcd-web:
>   envFrom:
>     - secretRef:
>         name: <vault-synced-secret-name>
> ```

**Do not proceed** with creating values.yaml containing hardcoded secrets. Wait for user confirmation that secrets have been added to Vault.

#### 2.3 Check bcd-web-chart Repository

Fetch the latest chart version from:
`https://gitlab.biocad.ru/biocad/dir/devops/bcd-helm-charts/bcd-web-chart`

Get available tags and select the latest stable version.

#### 2.4 Create Helm Structure

Create `helm/` folder in repository with:

**IMPORTANT**: Add `.gitignore` to exclude chart archives:
```gitignore
# Helm dependency charts (downloaded on build)
helm/charts/*.tgz
helm/Chart.lock
```

**Chart.yaml:**
```yaml
apiVersion: v2
name: APPLICATION_NAME
description: A Helm chart for APPLICATION_NAME
type: application
version: 0.1.0
appVersion: "no"
dependencies:
  - name: bcd-web
    version: <LATEST_CHART_TAG>
    repository: "https://charts.k8s.biocad.ru/"
```

**values.yaml:**

Map docker-compose values to chart values. Common mappings:

| Docker Compose | Helm values.yaml |
|----------------|------------------|
| `image:` | `bcd-web.image.repository`, `bcd-web.image.tag` |
| `ports:` | `bcd-web.service.port`, `bcd-web.containerPort` |
| `environment:` | `bcd-web.env` or `bcd-web.envFrom` |
| `volumes:` | `bcd-web.persistence` or `bcd-web.extraVolumes` |
| `deploy.resources:` | `bcd-web.resources.limits`, `bcd-web.resources.requests` |
| `replicas:` | `bcd-web.replicaCount` |

**MANDATORY: Default Security Capabilities**

Always include these capabilities in the container's securityContext:

```yaml
securityContext:
  capabilities:
    add:
      - CHOWN
      - DAC_OVERRIDE
      - NET_BIND_SERVICE
      - NET_RAW
      - SETGID
      - SETUID
      - FOWNER
      - MKNOD
```

For charts using `containers` structure, add to each container:
```yaml
bcd-web:
  containers:
    <container-name>:
      securityContext:
        capabilities:
          add:
            - CHOWN
            - DAC_OVERRIDE
            - NET_BIND_SERVICE
            - NET_RAW
            - SETGID
            - SETUID
            - FOWNER
            - MKNOD
```

#### 2.5 Create GitLab CI Pipeline

Create `.gitlab-ci.yml` with deploy stages:

```yaml
stages:
  - build
  - deploy

variables:
  HELM_RELEASE_NAME: "${CI_PROJECT_NAME}"
  KUBERNETES_NAMESPACE: "${CI_PROJECT_NAME}"

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main
    - master

deploy:
  stage: deploy
  image: alpine/helm:latest
  script:
    - helm dependency update ./helm
    - helm upgrade --install $HELM_RELEASE_NAME ./helm 
        --namespace $KUBERNETES_NAMESPACE 
        --create-namespace
        --set bcd-web.image.tag=$CI_COMMIT_SHA
  only:
    - main
    - master
  environment:
    name: production
```

### Step 3: Report

When batch complete:

1. **Show what was implemented**:
   - List created files
   - Summarize key configurations
   
2. **Show verification output**:
   - Helm lint results if available
   - YAML validation status

3. Say: **"Ready for feedback."**

### Step 4: Continue

Based on feedback:

1. Apply requested changes
2. Execute next batch if needed
3. Repeat until complete

## Checklist Template

Copy this checklist for TodoWrite:

```
- [ ] Analyze docker-compose files
- [ ] Check for sensitive data (.env, secrets)
- [ ] Notify user about Vault if secrets found
- [ ] Fetch latest bcd-web-chart version
- [ ] Create helm/Chart.yaml
- [ ] Create helm/values.yaml
- [ ] Add MANDATORY securityContext.capabilities to all containers
- [ ] Create .gitignore (exclude *.tgz, Chart.lock)
- [ ] Create .gitlab-ci.yml
- [ ] Validate configurations
- [ ] Report to user
```

## Common Values Reference

For detailed bcd-web-chart values reference, see [values-reference.md](values-reference.md).

## Example Transformation

See [examples.md](examples.md) for complete docker-compose to Helm conversion examples.
