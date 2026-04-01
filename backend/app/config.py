from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/niyog_db"

    # LLM (LM Studio - OpenAI compatible)
    LM_STUDIO_BASE_URL: str = "http://localhost:1234/v1"
    LM_STUDIO_MODEL: str = "local-model"
    LM_STUDIO_API_KEY: str = ""  # Empty for local LLM

    # Supabase (optional)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "onboarding-files"

    # FastAPI
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: Literal["development", "production"] = "development"

    # Session
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
