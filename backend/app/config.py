import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/video_translator"
    DATABASE_USER: str = "user"
    DATABASE_PASSWORD: str = "password"
    DATABASE_NAME: str = "video_translator"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # App
    API_V1_STR: str = "/api/v1"
    APP_NAME: str = "Video Translator API"
    DEBUG: bool = True
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 5000000000  # 5GB
    UPLOAD_DIR: str = "./uploads"
    PROCESSED_DIR: str = "./processed"
    
    # Whisper
    WHISPER_MODEL: str = "base"  # tiny, base, small, medium, large
    WHISPER_DEVICE: str = "cuda"  # cuda or cpu
    
    # Translation
    TRANSLATION_API: str = "google"  # google or azure
    GOOGLE_TRANSLATE_API_KEY: str = ""
    
    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
