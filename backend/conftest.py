"""
Pytest configuration for video-translator backend tests.

Ensures .env is loaded and settings are properly mocked before any imports.
This must run BEFORE pytest collects any test modules.
"""

import os
import sys
from pathlib import Path


def _load_env_variables():
    """Load environment variables from .env file."""
    backend_dir = Path(__file__).parent.absolute()
    env_file = backend_dir / ".env"
    
    # Change working directory to backend if needed
    if Path.cwd() != backend_dir:
        os.chdir(backend_dir)
    
    # Default values if not in .env
    defaults = {
        'DATABASE_URL': 'postgresql://user:password@localhost:5432/video_translator',
        'REDIS_URL': 'redis://localhost:6379/0',
        'SECRET_KEY': 'test-secret-key',
        'MEDIA_ROOT': '/tmp/media',
        'PROCESSED_DIR': '/tmp/processed',
        'CELERY_BROKER_URL': 'redis://localhost:6379/0',
        'CELERY_RESULT_BACKEND': 'redis://localhost:6379/0',
        'UPLOAD_DIR': '/tmp/uploads',
        'UPLOAD_DIR': './uploads',
    }
    
    # Set defaults first
    for key, value in defaults.items():
        if key not in os.environ:
            os.environ[key] = value
    
    # Load .env if it exists (overrides defaults)
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    os.environ[key] = value


# Add backend to sys.path BEFORE any imports
backend_dir = Path(__file__).parent.absolute()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# CRITICAL: Load env variables BEFORE pytest does anything
_load_env_variables()

# Import pydantic settings to create mock
from pydantic_settings import BaseSettings, SettingsConfigDict


# Create a mock settings object with all required fields
class MockSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra='allow'  # Allow extra fields from .env
    )
    # From app.core.config
    DATABASE_URL: str = os.environ.get('DATABASE_URL', 'postgresql://localhost/video_translator')
    REDIS_URL: str = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'test-key')
    MEDIA_ROOT: str = os.environ.get('MEDIA_ROOT', '/tmp/media')
    PROCESSED_DIR: str = os.environ.get('PROCESSED_DIR', '/tmp/processed')
    CELERY_BROKER_URL: str = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND: str = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    TRANSLATOR_MODEL: str = 'facebook/m2m100_418M'
    TRANSLATOR_PROVIDER: str = 'local'
    TRANSLATOR_API_FALLBACK: bool = False
    HF_HOME: str = '/cache/huggingface'
    PROJECT_NAME: str = 'video-translator-backend'
    DEBUG: bool = False
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # From app.config
    UPLOAD_DIR: str = os.environ.get('UPLOAD_DIR', './uploads')
    MAX_UPLOAD_SIZE: int = 5000000000
    WHISPER_MODEL: str = 'base'
    WHISPER_DEVICE: str = 'cpu'  # Use cpu for tests
    GOOGLE_TRANSLATE_API_KEY: str = ''
    API_V1_STR: str = '/api/v1'
    APP_NAME: str = 'Video Translator API'
    ALLOWED_ORIGINS: list = ['http://localhost:3000', 'http://localhost:8000']
    DATABASE_USER: str = 'user'
    DATABASE_PASSWORD: str = 'password'
    DATABASE_NAME: str = 'video_translator'
    TRANSLATION_API: str = 'google'


# Create a single mock settings instance
_mock_settings = MockSettings()

# Monkeypatch both config modules BEFORE they're imported elsewhere
def patch_config_modules():
    """Monkeypatch both config modules to use mock settings."""
    
    # app.config module
    try:
        import app.config as app_config_module
        app_config_module.get_settings = lambda: _mock_settings
    except Exception as e:
        pass
    
    # app.core.config module
    try:
        import app.core.config as core_config_module
        core_config_module.get_settings = lambda: _mock_settings
    except Exception as e:
        pass


# Call patch before pytest_configure
patch_config_modules()


def pytest_configure(config):
    """Pytest configure hook - ensure env and patches are loaded."""
    _load_env_variables()
    patch_config_modules()

