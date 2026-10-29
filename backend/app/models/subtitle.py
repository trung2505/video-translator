import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.models import Base


class Subtitle(Base):
    __tablename__ = "subtitles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False)
    srt_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
