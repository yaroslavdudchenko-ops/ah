import json
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Optional


_CORS_DEFAULTS = ["http://localhost", "http://localhost:3000", "http://localhost:5173"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        # Treat empty-string env vars as None — prevents json.loads("") crash
        # in pydantic-settings ≥ 2.1 when CORS_ORIGINS="" is set in Dokploy UI.
        env_parse_none_str="",
    )

    DATABASE_URL: str = "postgresql+asyncpg://app:app@db:5432/protocols"

    AI_GATEWAY_URL: str = "http://localhost:8080"
    AI_GATEWAY_API_KEY: str = "dev-key"
    AI_GATEWAY_MODEL: str = "InHouse/Qwen3.5-122B"
    AI_GATEWAY_TIMEOUT: int = 90

    # Embeddings (RAG) — optional; if empty, RAG is silently disabled
    AI_EMBEDDING_URL: Optional[str] = None
    AI_EMBEDDING_MODEL: str = "InHouse/embeddings-model-1"
    AI_EMBEDDING_DIMS: int = 1536
    AI_EMBEDDING_TIMEOUT: int = 30
    RAG_SIMILARITY_THRESHOLD: float = 0.65
    RAG_TOP_K: int = 3

    APP_ENV: str = "development"
    LOG_LEVEL: str = "info"
    CORS_ORIGINS: Optional[List[str]] = None

    # Auth
    SECRET_KEY: str = "change-me-in-staging-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # Demo users: plain passwords — overridable via env
    ADMIN_PASSWORD: str = "admin123"
    EMPLOYEE_PASSWORD: str = "employee123"
    AUDITOR_PASSWORD: str = "auditor123"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if v is None:
            return _CORS_DEFAULTS
        if isinstance(v, list):
            return v or _CORS_DEFAULTS
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return _CORS_DEFAULTS
            # JSON array format: ["https://app.example.com"]
            if v.startswith("["):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return parsed or _CORS_DEFAULTS
                except json.JSONDecodeError:
                    pass
            # Comma-separated format: https://app.example.com,https://api.example.com
            return [o.strip() for o in v.split(",") if o.strip()] or _CORS_DEFAULTS
        return _CORS_DEFAULTS


settings = Settings()
