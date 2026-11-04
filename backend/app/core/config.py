"""Application configuration using Pydantic Settings."""
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_name: str = "EduMind AI"
    app_env: str = "development"
    debug: bool = True
    api_v1_str: str = "/api/v1"
    backend_cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Security
    secret_key: str = Field(default="change-me-development-secret-key")
    refresh_secret_key: str = Field(default="change-me-development-refresh-secret-key")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://edumind:edumind_password@localhost:5432/edumind"
    )
    test_database_url: str = Field(
        default="postgresql+asyncpg://edumind:edumind_password@localhost:5432/edumind_test"
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Cookies
    session_cookie_name: str = "edumind_session"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    csrf_cookie_name: str = "edumind_csrf"

    # File upload
    max_upload_size_mb: int = 10
    upload_storage_path: str = "./uploads"

    # i18n
    default_locale: str = "uz"
    available_locales: List[str] = ["uz", "ru", "en"]

    # Super admin bootstrap (development only)
    super_admin_email: str = "admin@edumind.uz"
    super_admin_password: str = "ChangeMeSuperAdmin123!"

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def _parse_cors(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @field_validator("available_locales", mode="before")
    @classmethod
    def _parse_locales(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
