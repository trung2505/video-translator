import uuid
from sqlalchemy import Column, Float, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models import Base


class Segment(Base):
    __tablename__ = "segments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("translation_jobs.id"), nullable=False)
    start = Column(Float, nullable=False)
    end = Column(Float, nullable=False)
    original_text = Column(String, nullable=True)
    translated_text = Column(String, nullable=True)
    order_index = Column(Integer, nullable=True)

    job = relationship("TranslationJob")
