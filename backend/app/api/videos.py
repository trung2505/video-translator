import os
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import get_settings
from app import models
from app.schemas.video import VideoCreateResponse, VideoStatusResponse
import shutil
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/v1/videos", tags=["videos"])
settings = get_settings()


@router.post("/", response_model=VideoCreateResponse)
def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Save uploaded file to MEDIA_ROOT
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    file_id = uuid.uuid4()
    out_path = os.path.join(settings.MEDIA_ROOT, f"{file_id}_{file.filename}")
    with open(out_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    fr = models.FileRecord(file_type="video", path=out_path, size=None, mime_type=file.content_type)
    db.add(fr)
    db.commit()
    db.refresh(fr)

    # Create video record
    vid = models.Video(user_id=uuid.UUID(int=0), original_file_id=fr.id, title=file.filename)
    db.add(vid)
    db.commit()
    db.refresh(vid)

    # Create translation job record (queued status)
    job = models.TranslationJob(video_id=vid.id, status=models.TranslationJobStatus.QUEUED.value)
    db.add(job)
    db.commit()
    db.refresh(job)

    # Enqueue pipeline: extract_audio_task
    # Note: task_id, started_at, finished_at will be set by the task itself
    from app.workers.tasks import extract_audio_task
    extract_audio_task.delay(str(job.id), str(vid.id), out_path)

    return {"id": vid.id, "message": "uploaded"}


@router.get("/{video_id}/status", response_model=VideoStatusResponse)
def video_status(video_id: str, db: Session = Depends(get_db)):
    vid = db.query(models.Video).filter(models.Video.id == video_id).first()
    if not vid:
        raise HTTPException(status_code=404, detail="Video not found")
    job = db.query(models.TranslationJob).filter(models.TranslationJob.video_id == vid.id).order_by(models.TranslationJob.created_at.desc()).first()
    return {
        "video_id": vid.id,
        "video_status": vid.status,
        "video_progress": vid.progress or 0,
        "job_id": job.id if job else None,
        "job_status": job.status if job else None,
    }
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.database import get_db
from app.services.video_service import VideoService
from app.models import Video, VideoStatus
from app.api.schemas import VideoResponse
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/videos", tags=["videos"])

@router.post("/upload", response_model=VideoResponse)
async def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a video file"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid file")
    
    video = VideoService.save_upload_file(file, db)
    return video

@router.get("", response_model=list[VideoResponse])
def list_videos(db: Session = Depends(get_db)):
    """List all videos"""
    videos = VideoService.list_videos(db)
    return videos

@router.get("/{video_id}", response_model=VideoResponse)
def get_video(video_id: str, db: Session = Depends(get_db)):
    """Get video by ID"""
    video = VideoService.get_video(video_id, db)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.get("/{video_id}/status", response_model=VideoStatusResponse)
def get_video_status(video_id: str, db: Session = Depends(get_db)):
    """Get video processing status and related latest translation job"""
    video = VideoService.get_video(video_id, db)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Get latest translation job for this video, if any
    job = db.query(TranslationJob).filter(TranslationJob.video_id == video_id).order_by(TranslationJob.created_at.desc()).first()

    return {
        "video_id": video.id,
        "video_status": video.status.value if hasattr(video.status, 'value') else str(video.status),
        "video_progress": int(video.progress or 0),
        "job_id": job.id if job else None,
        "job_status": job.status.value if job and hasattr(job.status, 'value') else (str(job.status) if job else None)
    }

@router.delete("/{video_id}")
def delete_video(video_id: str, db: Session = Depends(get_db)):
    """Delete a video"""
    video = VideoService.get_video(video_id, db)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Delete file
    import os
    if os.path.exists(video.file_path):
        os.remove(video.file_path)
    
    db.delete(video)
    db.commit()
    
    return {"message": "Video deleted"}
