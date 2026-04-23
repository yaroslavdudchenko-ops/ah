from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+asyncpg://app:app@db:5432/protocols"

    AI_GATEWAY_URL: str = "http://localhost:8080"
    AI_GATEWAY_API_KEY: str = "dev-key"
    AI_GATEWAY_MODEL: str = "InHouse/Qwen3.5-122B"
    AI_GATEWAY_TIMEOUT: int = 90

    APP_ENV: str = "development"
    LOG_LEVEL: str = "info"
    CORS_ORIGINS: List[str] = ["http://localhost", "http://localhost:3000", "http://localhost:5173"]

    # Auth
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # Demo users: plain passwords — overridable via env
    ADMIN_PASSWORD: str = "admin123"
    EMPLOYEE_PASSWORD: str = "employee123"
    AUDITOR_PASSWORD: str = "auditor123"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",")]
        return v


settings = Settings()
