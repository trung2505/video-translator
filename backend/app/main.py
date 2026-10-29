from fastapi import FastAPI
from app.api import videos, tts
from app.core.config import get_settings

def create_app() -> FastAPI:
    from app.api import auth

    app = FastAPI(title=get_settings().PROJECT_NAME)
    app.include_router(auth.router)
    app.include_router(videos.router)
    app.include_router(tts.router)
    @app.get('/health')
    def health():
        return {"status": "ok"}
    return app


from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging

from app.config import get_settings
from app.database import engine, Base
from app.models import Video, TranslationJob
from app.api import auth, videos, translations, health, tts
from app.workers.tasks import celery_app

# Create tables
Base.metadata.create_all(bind=engine)

settings = get_settings()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="API for translating Chinese videos to Vietnamese",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])

# Routes
app.include_router(auth.router)
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(videos.router, prefix=settings.API_V1_STR)
app.include_router(translations.router, prefix=settings.API_V1_STR)
app.include_router(tts.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup")
    logger.info(f"CORS origins: {settings.ALLOWED_ORIGINS}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
