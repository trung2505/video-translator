import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import get_settings

settings = get_settings()

# Create directories if they don't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)

engine = create_engine(settings.DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
