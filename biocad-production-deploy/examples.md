# Transformation Examples

## Example 1: Simple Web Application

### Input: docker-compose.yml

```yaml
version: '3.8'

services:
  webapp:
    image: registry.biocad.ru/project/webapp:1.2.3
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgres://db:5432/mydb
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=info
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.1'
          memory: 128M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Output: helm/Chart.yaml

```yaml
apiVersion: v2
name: webapp
description: A Helm chart for webapp
type: application
version: 0.1.0
appVersion: "1.2.3"
dependencies:
  - name: bcd-web
    version: 1.5.0
    repository: "https://charts.k8s.biocad.ru/"
```

### Output: .gitignore

```gitignore
# Helm dependency charts (downloaded on build)
helm/charts/*.tgz
helm/Chart.lock
```

### Output: helm/values.yaml

```yaml
bcd-web:
  replicaCount: 2

  image:
    repository: registry.biocad.ru/project/webapp
    tag: "1.2.3"
    pullPolicy: IfNotPresent

  containerPort: 8080

  service:
    type: ClusterIP
    port: 8080

  env:
    - name: DATABASE_URL
      value: "postgres://db:5432/mydb"
    - name: REDIS_URL
      value: "redis://redis:6379"
    - name: LOG_LEVEL
      value: "info"

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

  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 100m
      memory: 128Mi

  livenessProbe:
    httpGet:
      path: /health
      port: http
    initialDelaySeconds: 30
    periodSeconds: 30
    timeoutSeconds: 10
    failureThreshold: 3

  readinessProbe:
    httpGet:
      path: /health
      port: http
    initialDelaySeconds: 5
    periodSeconds: 10
```

---

## Example 2: Application with Secrets and Volumes

### Input: docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    image: registry.biocad.ru/project/api:2.0.0
    ports:
      - "3000:3000"
    env_file:
      - .env.production
    volumes:
      - ./config:/app/config:ro
      - data:/app/data
    secrets:
      - db_password
      - api_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_key:
    file: ./secrets/api_key.txt

volumes:
  data:
```

### Output: helm/Chart.yaml

```yaml
apiVersion: v2
name: api
description: A Helm chart for api
type: application
version: 0.1.0
appVersion: "2.0.0"
dependencies:
  - name: bcd-web
    version: 1.5.0
    repository: "https://charts.k8s.biocad.ru/"
```

### Output: helm/values.yaml

```yaml
bcd-web:
  replicaCount: 1

  image:
    repository: registry.biocad.ru/project/api
    tag: "2.0.0"
    pullPolicy: IfNotPresent

  containerPort: 3000

  service:
    type: ClusterIP
    port: 3000

  envFrom:
    - secretRef:
        name: api-secrets
    - configMapRef:
        name: api-config

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

  persistence:
    enabled: true
    storageClass: "standard"
    accessMode: ReadWriteOnce
    size: 5Gi
    mountPath: /app/data

  extraVolumes:
    - name: config
      configMap:
        name: api-config-files

  extraVolumeMounts:
    - name: config
      mountPath: /app/config
      readOnly: true
```

### Additional: Create Kubernetes Secret

```bash
kubectl create secret generic api-secrets \
  --from-file=DB_PASSWORD=./secrets/db_password.txt \
  --from-file=API_KEY=./secrets/api_key.txt
```

---

## Example 3: Multi-Container Application

### Input: docker-compose.yml

```yaml
version: '3.8'

services:
  frontend:
    image: registry.biocad.ru/project/frontend:1.0.0
    ports:
      - "80:80"
    depends_on:
      - backend

  backend:
    image: registry.biocad.ru/project/backend:1.0.0
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgres://db:5432/app
```

### Output: Separate Helm Charts

For multi-container applications, create separate charts or use subcharts:

**helm/Chart.yaml:**
```yaml
apiVersion: v2
name: myapp
description: A Helm chart for myapp
type: application
version: 0.1.0
appVersion: "1.0.0"
dependencies:
  - name: bcd-web
    version: 1.5.0
    repository: "https://charts.k8s.biocad.ru/"
    alias: frontend
  - name: bcd-web
    version: 1.5.0
    repository: "https://charts.k8s.biocad.ru/"
    alias: backend
```

**helm/values.yaml:**
```yaml
frontend:
  image:
    repository: registry.biocad.ru/project/frontend
    tag: "1.0.0"
  containerPort: 80
  service:
    port: 80

backend:
  image:
    repository: registry.biocad.ru/project/backend
    tag: "1.0.0"
  containerPort: 8080
  service:
    port: 8080
  env:
    - name: DATABASE_URL
      value: "postgres://db:5432/app"
```

---

## GitLab CI/CD Examples

### Basic Pipeline

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
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker build -t $CI_REGISTRY_IMAGE:latest .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - docker push $CI_REGISTRY_IMAGE:latest
  only:
    - main

deploy:
  stage: deploy
  image: alpine/helm:latest
  before_script:
    - helm repo add biocad https://charts.k8s.biocad.ru/
    - helm repo update
  script:
    - helm dependency update ./helm
    - |
      helm upgrade --install $HELM_RELEASE_NAME ./helm \
        --namespace $KUBERNETES_NAMESPACE \
        --create-namespace \
        --set bcd-web.image.tag=$CI_COMMIT_SHA \
        --wait --timeout 5m
  only:
    - main
  environment:
    name: production
    url: https://$CI_PROJECT_NAME.biocad.ru
```

### Pipeline with Multiple Environments

```yaml
stages:
  - build
  - deploy-staging
  - deploy-production

.deploy_template: &deploy_template
  image: alpine/helm:latest
  before_script:
    - helm repo add biocad https://charts.k8s.biocad.ru/
    - helm repo update
  script:
    - helm dependency update ./helm
    - |
      helm upgrade --install $HELM_RELEASE_NAME ./helm \
        --namespace $KUBERNETES_NAMESPACE \
        --create-namespace \
        --set bcd-web.image.tag=$CI_COMMIT_SHA \
        -f ./helm/values-${ENVIRONMENT}.yaml \
        --wait --timeout 5m

deploy-staging:
  <<: *deploy_template
  stage: deploy-staging
  variables:
    ENVIRONMENT: staging
    KUBERNETES_NAMESPACE: "${CI_PROJECT_NAME}-staging"
  environment:
    name: staging
  only:
    - main

deploy-production:
  <<: *deploy_template
  stage: deploy-production
  variables:
    ENVIRONMENT: production
    KUBERNETES_NAMESPACE: "${CI_PROJECT_NAME}"
  environment:
    name: production
  when: manual
  only:
    - main
```
