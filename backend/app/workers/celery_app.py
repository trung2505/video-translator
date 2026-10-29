from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("video_translator")
celery_app.conf.include = ["app.workers.tasks"]
celery_app.conf.broker_url = settings.REDIS_URL
celery_app.conf.result_backend = settings.REDIS_URL
