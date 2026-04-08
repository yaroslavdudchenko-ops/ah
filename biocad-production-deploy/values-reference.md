# bcd-web-chart Values Reference

Common values for the `bcd-web` dependency chart.

## Image Configuration

```yaml
bcd-web:
  image:
    repository: registry.biocad.ru/project/app
    tag: latest
    pullPolicy: IfNotPresent
  imagePullSecrets:
    - name: registry-secret
```

## Replicas and Scaling

```yaml
bcd-web:
  replicaCount: 2
  
  autoscaling:
    enabled: false
    minReplicas: 1
    maxReplicas: 10
    targetCPUUtilizationPercentage: 80
```

## Service Configuration

```yaml
bcd-web:
  service:
    type: ClusterIP
    port: 80
  
  containerPort: 8080
```

## Ingress Configuration

```yaml
bcd-web:
  ingress:
    enabled: true
    className: nginx
    annotations:
      nginx.ingress.kubernetes.io/ssl-redirect: "true"
    hosts:
      - host: app.biocad.ru
        paths:
          - path: /
            pathType: Prefix
    tls:
      - secretName: app-tls
        hosts:
          - app.biocad.ru
```

## Environment Variables

```yaml
bcd-web:
  env:
    - name: DATABASE_URL
      value: "postgres://localhost:5432/db"
    - name: LOG_LEVEL
      value: "info"
  
  envFrom:
    - secretRef:
        name: app-secrets
    - configMapRef:
        name: app-config
```

## Resources

```yaml
bcd-web:
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 100m
      memory: 256Mi
```

## Persistence

```yaml
bcd-web:
  persistence:
    enabled: true
    storageClass: "standard"
    accessMode: ReadWriteOnce
    size: 10Gi
    mountPath: /data
```

## Extra Volumes

```yaml
bcd-web:
  extraVolumes:
    - name: config
      configMap:
        name: app-config
  
  extraVolumeMounts:
    - name: config
      mountPath: /etc/app
      readOnly: true
```

## Health Checks

```yaml
bcd-web:
  livenessProbe:
    httpGet:
      path: /health
      port: http
    initialDelaySeconds: 30
    periodSeconds: 10
  
  readinessProbe:
    httpGet:
      path: /ready
      port: http
    initialDelaySeconds: 5
    periodSeconds: 5
```

## Node Selection

```yaml
bcd-web:
  nodeSelector:
    kubernetes.io/os: linux
  
  tolerations: []
  
  affinity: {}
```

## Security Context

```yaml
bcd-web:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
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
  
  podSecurityContext:
    fsGroup: 1000
```

**Default capabilities** (add to all deployments):
```yaml
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

## Service Account

```yaml
bcd-web:
  serviceAccount:
    create: true
    name: ""
    annotations: {}
```
