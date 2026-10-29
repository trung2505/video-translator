from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
import os

from app.db.session import get_db
from app.models import TranslationJob, TranslationJobStatus, Video, VideoStatus
from app.api.schemas import TranslationJobResponse, TranslationStartRequest, TranslationStartResponse
from app.workers.tasks import extract_audio_task
from app.core.config import get_settings
from app.services.video_service import VideoService

settings = get_settings()
router = APIRouter(prefix="/translations", tags=["translations"])

@router.post("", response_model=TranslationStartResponse)
def start_translation(request: TranslationStartRequest, db: Session = Depends(get_db)):
    """Start a translation job using the standard pipeline."""
    # Check if video exists
    video = db.query(Video).filter(Video.id == request.video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Create translation job (starts in QUEUED status)
    job = TranslationJob(
        video_id=request.video_id,
        status=TranslationJobStatus.QUEUED.value
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Mark video as processing
    video.status = VideoStatus.PROCESSING.value
    db.add(video)
    db.commit()

    # Start async pipeline with extract_audio_task
    original_file_path = video.original_file.path
    extract_audio_task.delay(str(job.id), str(video.id), original_file_path)
    
    return {
        "id": str(job.id),
        "video_id": str(request.video_id),
        "status": job.status,
        "message": "Translation started"
    }

@router.get("/{job_id}", response_model=TranslationJobResponse)
def get_translation_status(job_id: str, db: Session = Depends(get_db)):
    """Get translation job status"""
    job = db.query(TranslationJob).filter(TranslationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/{job_id}/download")
def download_translated_video(job_id: str, db: Session = Depends(get_db)):
    """Download translated video"""
    job = db.query(TranslationJob).filter(TranslationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != TranslationJobStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Translation not completed")
    
    # Get video and check for processed file
    video = db.query(Video).filter(Video.id == job.video_id).first()
    if not video or not video.processed_file_id:
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        path=video.processed_file.path,
        media_type='video/mp4',
        filename=f"translated_video_{job_id}.mp4"
    )

@router.get("/{job_id}/subtitles")
def download_subtitles(job_id: str, db: Session = Depends(get_db)):
    """Download subtitles"""
    job = db.query(TranslationJob).filter(TranslationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get video and check for subtitle file
    video = db.query(Video).filter(Video.id == job.video_id).first()
    if not video or not video.subtitle_file_id:
        raise HTTPException(status_code=404, detail="Subtitles not found")
    
    return FileResponse(
        path=video.subtitle_file.path,
        media_type='text/plain',
        filename=f"subtitles_{job_id}.srt"
    )
