import os
import uuid
from pathlib import Path
from app.config import get_settings
from app.models import Video, VideoStatus
from sqlalchemy.orm import Session

settings = get_settings()

class VideoService:
    @staticmethod
    def save_upload_file(file, db: Session) -> Video:
        """Save uploaded video file and create database record"""
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{file_extension}")
        
        # Save file to disk
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
        
        file_size = os.path.getsize(file_path)
        
        # Create database record
        video = Video(
            id=file_id,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            status=VideoStatus.uploaded,
            progress=0
        )
        
        db.add(video)
        db.commit()
        db.refresh(video)
        
        return video
    
    @staticmethod
    def get_video(video_id: str, db: Session) -> Video:
        """Get video by ID"""
        return db.query(Video).filter(Video.id == video_id).first()
    
    @staticmethod
    def list_videos(db: Session):
        """List all videos"""
        return db.query(Video).all()
    
    @staticmethod
    def update_video_status(video_id: str, status: VideoStatus, db: Session):
        """Update video status"""
        video = VideoService.get_video(video_id, db)
        if video:
            video.status = status
            db.commit()
            db.refresh(video)
        return video
