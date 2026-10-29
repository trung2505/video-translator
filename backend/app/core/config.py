from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyUrl, Field
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    PROJECT_NAME: str = "video-translator-backend"
    DEBUG: bool = False

    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    REDIS_URL: str = Field(default="redis://redis:6379/0", env="REDIS_URL")

    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    MEDIA_ROOT: str = str(Path(__file__).resolve().parents[3] / "storage")
    PROCESSED_DIR: str = str(Path(MEDIA_ROOT) / "processed")

    CELERY_BROKER_URL: str = Field(default=None, env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default=None, env="CELERY_RESULT_BACKEND")
    # Hugging Face cache directory for models
    HF_HOME: str = "/cache/huggingface"
    # Local translator model name
    TRANSLATOR_MODEL: str = "facebook/m2m100_418M"
    # Translator provider option: local or api
    TRANSLATOR_PROVIDER: str = "local"
    # Whether to allow API fallback when local translation returns empty
    TRANSLATOR_API_FALLBACK: bool = False


def get_settings() -> Settings:
    return Settings()
