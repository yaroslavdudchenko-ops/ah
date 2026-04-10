# Dockerfile Templates

Production-ready Dockerfile templates per language. All templates follow bcd-web requirements:
- Multi-stage builds (build + runtime)
- Non-root user UID/GID 1000 (`USER 1000:1000`)
- Minimal base images
- `EXPOSE` with actual port
- `HEALTHCHECK` instruction

## Go

```dockerfile
FROM golang:1.22-alpine AS build
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /bin/service ./cmd/service

FROM gcr.io/distroless/static:nonroot
COPY --from=build /bin/service /service
USER 1000:1000
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s CMD ["/service", "healthcheck"]
ENTRYPOINT ["/service"]
```

## Python

```dockerfile
FROM python:3.12-slim AS build
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=build /install /usr/local
COPY . .
RUN useradd -u 1000 -U app
USER 1000:1000
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
ENTRYPOINT ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Node.js

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:20-alpine
WORKDIR /app
COPY --from=build /app/node_modules ./node_modules
COPY . .
USER 1000:1000
EXPOSE 3000
HEALTHCHECK --interval=15s --timeout=5s CMD ["node", "-e", "require('http').get('http://localhost:3000/health', r => r.statusCode === 200 ? process.exit(0) : process.exit(1))"]
ENTRYPOINT ["node", "src/index.js"]
```

## Java (Spring Boot)

```dockerfile
FROM eclipse-temurin:21-jdk-alpine AS build
WORKDIR /app
COPY gradlew build.gradle settings.gradle ./
COPY gradle ./gradle
RUN ./gradlew dependencies --no-daemon
COPY src ./src
RUN ./gradlew bootJar --no-daemon

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=build /app/build/libs/*.jar app.jar
RUN adduser -u 1000 -D app
USER 1000:1000
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s CMD ["wget", "-qO-", "http://localhost:8080/actuator/health"]
ENTRYPOINT ["java", "-jar", "app.jar"]
```

## .NET

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:8.0-alpine AS build
WORKDIR /app
COPY *.csproj ./
RUN dotnet restore
COPY . .
RUN dotnet publish -c Release -o /out --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:8.0-alpine
WORKDIR /app
COPY --from=build /out .
RUN adduser -u 1000 -D app
USER 1000:1000
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s CMD ["wget", "-qO-", "http://localhost:8080/health"]
ENTRYPOINT ["dotnet", "App.dll"]
```

## .dockerignore (universal)

Generate alongside every Dockerfile:

```
.git
.gitignore
.env
*.md
docker-compose*.yml
helm/
.gitlab-ci.yml
node_modules
__pycache__
*.pyc
.venv
bin/
obj/
build/
dist/
.idea
.vscode
```
