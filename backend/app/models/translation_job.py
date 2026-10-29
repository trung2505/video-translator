import uuid
from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from enum import Enum
from app.models import Base


class TranslationJobStatus(str, Enum):
    """TranslationJob lifecycle states."""
    QUEUED = "queued"       # Job created, waiting to be picked up
    RUNNING = "running"     # Job is currently processing
    COMPLETED = "completed" # Job finished successfully
    FAILED = "failed"       # Job failed with error


class TranslationJob(Base):
    __tablename__ = "translation_jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Standalone text-to-speech jobs do not have a source video.
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=True)
    # New fields to support text/image/video jobs
    job_type = Column(String(50), nullable=False, default="video")
    input_file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=True)
    output_file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=True)
    task_id = Column(String, nullable=True)  # Celery task ID (set when job is enqueued)
    status = Column(String, default=TranslationJobStatus.QUEUED.value)
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    parameters = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)  # Set when job starts processing
    finished_at = Column(DateTime(timezone=True), nullable=True)  # Set when job completes or fails
