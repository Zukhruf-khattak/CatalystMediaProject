from functools import lru_cache
from typing import List, Literal, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application Metadata
    app_name: str = Field(
        default="Catalist Meeting Intelligence",
        description="Public display name of the application",
    )
    app_env: Literal["development", "testing", "staging", "production"] = Field(
        default="development",
        description="Deployment environment name",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode and detailed logs",
    )
    api_v1_prefix: str = Field(
        default="/api/v1",
        description="Routing prefix for v1 API endpoints",
    )
    app_version: str = Field(
        default="0.1.0",
        description="Semantic version of the application",
    )

    # Server Bindings
    backend_host: str = Field(
        default="0.0.0.0",
        description="Host interface for server to bind",
    )
    backend_port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="Port for server to listen on",
    )

    # CORS Configuration
    allowed_origins: Union[List[str], str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
        description="List of allowed CORS origins or comma-separated string",
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        raise ValueError("allowed_origins must be a list of strings or comma-separated string")

    # Database Configuration (PostgreSQL 16 + pgvector)
    database_url: str = Field(
        default="postgresql+psycopg://catalist_user:catalist_password@localhost:5432/catalist_db",
        description="Full SQLAlchemy database connection string",
    )
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_max_overflow: int = Field(default=10, ge=0, le=100)
    db_pool_timeout: int = Field(default=30, ge=1)
    db_pool_recycle: int = Field(default=1800, ge=60)

    # Observability - LangSmith Tracing
    langsmith_tracing: bool = Field(
        default=False,
        description="Whether LangSmith tracing is active",
    )
    langsmith_endpoint: str = Field(
        default="https://api.smith.langchain.com",
        description="LangSmith API endpoint",
    )
    langsmith_api_key: str = Field(
        default="",
        description="LangSmith API Key (optional for local execution)",
    )
    langsmith_project: str = Field(
        default="catalist-meeting-intelligence",
        description="LangSmith project name",
    )

    # Model Provider Settings
    llm_provider: Literal["ollama", "gemini", "mock"] = Field(
        default="ollama",
        description="Primary LLM provider (local-first)",
    )
    llm_model: str = Field(
        default="llama3.2",
        description="Default model identifier",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for local Ollama service",
    )
    gemini_api_key: str = Field(
        default="",
        description="Optional API key for Gemini free tier",
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging severity threshold",
    )
    log_format: Literal["json", "text"] = Field(
        default="json",
        description="Log output formatting style",
    )

    # Dataset & Ingestion Configuration (Phase 2)
    dataset_dir: str = Field(
        default="data/raw",
        description="Root directory containing raw meeting transcripts and questions",
    )
    dataset_archive_path: str = Field(
        default="data/raw/Catalist_AI_Intern_Build_Test_Data.zip",
        description="Path to supplied dataset zip archive",
    )
    archive_max_size_bytes: int = Field(
        default=52428800,  # 50 MB
        description="Maximum allowed compressed archive size in bytes",
    )
    archive_max_extracted_files: int = Field(
        default=500,
        description="Maximum number of files allowed in dataset extraction",
    )
    parser_version: str = Field(
        default="1.0.0",
        description="Deterministic transcript parser version tag",
    )
    fts_language_config: str = Field(
        default="english",
        description="PostgreSQL tsvector text search configuration",
    )

    # Embedding Configuration (sentence-transformers/all-MiniLM-L6-v2)
    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace model identifier for local embeddings",
    )
    embedding_dim: int = Field(
        default=384,
        description="Expected embedding vector dimension for all-MiniLM-L6-v2",
    )
    embedding_batch_size: int = Field(
        default=32,
        ge=1,
        le=256,
        description="Batch size for generating embeddings",
    )
    embedding_device: str = Field(
        default="cpu",
        description="Compute device for local embedding inference (cpu)",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
