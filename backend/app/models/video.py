import uuid
from sqlalchemy import Column, String, ForeignKey, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.models import Base


class VideoStatus(str, Enum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Video(Base):
    __tablename__ = "videos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=True)
    original_file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=False)
    processed_file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=True)
    subtitle_file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=True)
    status = Column(String, default=VideoStatus.UPLOADED.value, nullable=False)
    progress = Column(Integer, default=0)
    duration = Column(Float, nullable=True)
    language = Column(String(20), default="zh")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    original_file = relationship("FileRecord", foreign_keys=[original_file_id])
    processed_file = relationship("FileRecord", foreign_keys=[processed_file_id])
    subtitle_file = relationship("FileRecord", foreign_keys=[subtitle_file_id])
