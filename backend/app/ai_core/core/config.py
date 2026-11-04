"""AI Core configuration using Pydantic Settings."""
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class AICoreSettings(BaseSettings):
    # Feature flags
    ai_core_enabled: bool = True
    rag_enabled: bool = True
    mcp_enabled: bool = True
    cache_enabled: bool = True
    trace_enabled: bool = True

    # Model provider (no secrets here; secret via env var name only)
    default_llm_provider: Optional[str] = Field(default=None)
    default_embedding_provider: Optional[str] = Field(default=None)
    llm_provider_secret_env: Optional[str] = Field(default=None)  # env var NAME, not value
    embedding_provider_secret_env: Optional[str] = Field(default=None)

    # Providers
    enabled_providers: List[str] = []  # e.g. ["test", "stub"]

    # RAG limits
    max_document_size_mb: int = 25
    max_chunks_per_document: int = 2000
    default_chunk_size: int = 1000
    default_chunk_overlap: int = 200
    default_top_k: int = 10
    allowed_document_extensions: List[str] = [".pdf", ".docx", ".txt", ".md"]
    allowed_document_mimes: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/markdown",
    ]

    # Cache
    cache_default_ttl_seconds: int = 300
    cache_redis_db: int = 1  # separate DB index from Phase 1 (db 0)

    # Security
    rate_limit_per_minute: int = 60
    prompt_max_length: int = 4000

    # Trace
    trace_sample_rate: float = 1.0
    otel_endpoint: Optional[str] = None

    @field_validator("enabled_providers", "allowed_document_extensions", "allowed_document_mimes", mode="before")
    @classmethod
    def _parse_list(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
        env_prefix = "AI_"


@lru_cache
def get_ai_settings() -> AICoreSettings:
    return AICoreSettings()


ai_settings = get_ai_settings()
