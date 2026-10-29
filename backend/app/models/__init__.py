from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Import models from separate files
from app.models.video import Video, VideoStatus
from app.models.translation_job import TranslationJob, TranslationJobStatus
from app.models.file import FileRecord
from app.models.segment import Segment
from app.models.subtitle import Subtitle
from app.models.user import User

__all__ = [
    "Base",
    "Video",
    "VideoStatus",
    "TranslationJob",
    "TranslationJobStatus",
    "FileRecord",
    "Segment",
    "Subtitle",
    "User",
]
