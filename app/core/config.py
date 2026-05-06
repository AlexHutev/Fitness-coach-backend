from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Database — psycopg3 driver supports both sync (Alembic) and async (runtime).
    database_url: str = "postgresql+psycopg://fitness_coach:fitness_coach@localhost:5432/fitness_coach"

    # Security
    secret_key: str = "CHANGE_ME_IN_ENV_FILE"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    # CORS
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    # Environment
    environment: str = "development"

    # Email
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""

    # Rate limiting (requests per minute per IP for sensitive endpoints)
    auth_rate_limit_per_minute: int = 10

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_be_strong(cls, v: str, info) -> str:
        # Only enforce in non-development to keep local dev frictionless.
        env = (info.data.get("environment") or "development").lower()
        if env != "development" and (len(v) < 32 or v == "CHANGE_ME_IN_ENV_FILE"):
            raise ValueError(
                "SECRET_KEY must be at least 32 chars and not the default in non-development environments. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )
        return v


settings = Settings()
