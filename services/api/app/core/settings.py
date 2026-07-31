"""Validated environment-based application configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, Field, PostgresDsn, RedisDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings shared by HTTP handlers and dependency probes."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SHOPLENS_",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    api_v1_prefix: str = "/api/v1"
    cors_allowed_origins: list[AnyHttpUrl] = [
        AnyHttpUrl("http://localhost:3000"),
        AnyHttpUrl("http://127.0.0.1:3000"),
    ]
    database_url: PostgresDsn = PostgresDsn(
        "postgresql://shoplens:shoplens@127.0.0.1:5432/shoplens"
    )
    redis_url: RedisDsn = RedisDsn("redis://127.0.0.1:6379/0")
    object_storage_path: Path = Path("data/storage")
    dependency_timeout_seconds: float = Field(default=2.0, gt=0, le=30)
    cache_enabled: bool = True
    cache_ttl_seconds: int = Field(default=60, ge=1, le=3600)
    cache_namespace: str = Field(default="stage8-v1", min_length=1, max_length=64)
    rate_limit_enabled: bool = True
    rate_limit_requests: int = Field(default=120, ge=1, le=100_000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    provider_retry_attempts: int = Field(default=3, ge=1, le=5)
    provider_retry_backoff_seconds: float = Field(default=0.05, ge=0, le=5)
    circuit_breaker_failure_threshold: int = Field(default=3, ge=1, le=20)
    circuit_breaker_recovery_seconds: float = Field(default=30.0, gt=0, le=600)
    slow_query_threshold_ms: float = Field(default=100.0, gt=0, le=60_000)
    embedding_provider: Literal["fixture", "http"] = "fixture"
    embedding_endpoint: AnyHttpUrl | None = None
    embedding_api_key: str | None = None
    embedding_model_name: str = "BAAI/bge-m3"
    embedding_model_version: str = "fixture-semantic-v1"
    embedding_dimension: int = Field(default=1024, ge=1024, le=1024)
    embedding_batch_size: int = Field(default=16, ge=1, le=128)
    embedding_timeout_seconds: float = Field(default=10.0, gt=0, le=120)
    reranker_provider: Literal["fixture", "http"] = "fixture"
    reranker_endpoint: AnyHttpUrl | None = None
    reranker_api_key: str | None = None
    reranker_model_name: str = "BAAI/bge-reranker-v2-m3"
    reranker_model_version: str = "fixture-semantic-v1"
    reranker_timeout_seconds: float = Field(default=2.0, gt=0, le=30)
    image_embedding_provider: Literal["fixture", "http"] = "fixture"
    image_embedding_endpoint: AnyHttpUrl | None = None
    image_embedding_api_key: str | None = None
    image_embedding_model_name: str = "google/siglip2-base-patch16-224"
    image_embedding_model_version: str = "fixture-visual-v1"
    image_embedding_dimension: int = Field(default=768, ge=768, le=768)
    image_embedding_batch_size: int = Field(default=16, ge=1, le=128)
    image_embedding_timeout_seconds: float = Field(default=10.0, gt=0, le=120)
    image_candidate_k: int = Field(default=50, ge=1, le=100)
    multimodal_text_weight: float = Field(default=1.0, gt=0, le=10)
    multimodal_image_weight: float = Field(default=1.25, gt=0, le=10)
    image_upload_max_bytes: int = Field(default=5 * 1024 * 1024, ge=1024, le=20 * 1024 * 1024)
    image_upload_max_pixels: int = Field(default=20_000_000, ge=65_536, le=40_000_000)
    image_upload_max_dimension: int = Field(default=4096, ge=256, le=8192)
    lexical_candidate_k: int = Field(default=50, ge=1, le=100)
    dense_candidate_k: int = Field(default=50, ge=1, le=100)
    fusion_candidate_k: int = Field(default=30, ge=1, le=100)
    rerank_top_k: int = Field(default=30, ge=1, le=100)
    rrf_k: int = Field(default=60, ge=1, le=1000)
    agent_provider: Literal["fixture", "http"] = "fixture"
    agent_endpoint: AnyHttpUrl | None = None
    agent_api_key: str | None = None
    agent_model_name: str = "shoplens/bounded-shopping-agent"
    agent_model_version: str = "fixture-rules-v1"
    agent_timeout_seconds: float = Field(default=4.0, gt=0, le=60)
    agent_max_tool_steps: int = Field(default=4, ge=1, le=4)
    agent_result_limit: int = Field(default=3, ge=1, le=4)
    agent_session_ttl_seconds: int = Field(default=86_400, ge=300, le=2_592_000)
    agent_trace_ttl_seconds: int = Field(default=86_400, ge=300, le=604_800)

    @field_validator(
        "embedding_endpoint",
        "embedding_api_key",
        "reranker_endpoint",
        "reranker_api_key",
        "image_embedding_endpoint",
        "image_embedding_api_key",
        "agent_endpoint",
        "agent_api_key",
        mode="before",
    )
    @classmethod
    def empty_optional_provider_value_is_none(cls, value: object) -> object:
        """Accept Compose's empty optional environment values in offline Fixture mode."""

        return None if value == "" else value

    @model_validator(mode="after")
    def validate_provider_endpoints(self) -> "Settings":
        """Require explicit HTTP(S) endpoints only when a remote provider is selected."""

        if self.embedding_provider == "http" and self.embedding_endpoint is None:
            raise ValueError("embedding_endpoint is required for the HTTP embedding provider")
        if self.reranker_provider == "http" and self.reranker_endpoint is None:
            raise ValueError("reranker_endpoint is required for the HTTP reranker provider")
        if self.image_embedding_provider == "http" and self.image_embedding_endpoint is None:
            raise ValueError(
                "image_embedding_endpoint is required for the HTTP image embedding provider"
            )
        if self.agent_provider == "http" and self.agent_endpoint is None:
            raise ValueError("agent_endpoint is required for the HTTP agent provider")
        return self


@lru_cache
def get_settings() -> Settings:
    """Load and cache validated process configuration."""

    return Settings()
