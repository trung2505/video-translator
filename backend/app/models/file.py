import uuid
from sqlalchemy import Column, String, BigInteger, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.models import Base


class FileRecord(Base):
    __tablename__ = "files"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_type = Column(String(50), nullable=False)
    path = Column(String, nullable=False)
    size = Column(BigInteger, nullable=True)
    mime_type = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
