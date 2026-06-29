"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "AI Project Factory"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://factory:factory_dev@localhost:5432/ai_factory"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM
    llm_api_key: str = ""
    llm_provider: str = "claude"  # claude | openai
    llm_model: str = "claude-sonnet-4-20250514"
    llm_max_tokens: int = 16000
    llm_temperature: float = 0.1

    # File storage
    generated_files_dir: str = "./generated"
    uploaded_assets_dir: str = "./uploads"

    # Pipeline
    max_concurrent_projects: int = 5
    project_timeout_seconds: int = 600

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
