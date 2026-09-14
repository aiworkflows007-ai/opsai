"""Application configuration settings for OpsAI."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OpsAI"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # Database & Storage
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/opsai"
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "insecure-dev-secret-key-replace-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # LLM Settings
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    default_llm_model: str = "gpt-4o-mini"
    default_embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
