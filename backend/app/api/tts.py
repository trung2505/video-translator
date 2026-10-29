import json
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.schemas import TTSCreateRequest, TTSJobResponse
from app.db.session import get_db
from app.models import FileRecord, TranslationJob, TranslationJobStatus
from app.workers.tasks import synthesize_vietnamese_audio_task


router = APIRouter(prefix="/api/v1/tts", tags=["tts"])


def _response(job: TranslationJob) -> dict:
    parameters = json.loads(job.parameters or "{}")
    return {
        "id": str(job.id),
        "job_type": job.job_type,
        "status": job.status,
        "progress": job.progress or 0,
        "voice": parameters.get("voice", "female_young_adult"),
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "output_file_id": str(job.output_file_id) if job.output_file_id else None,
        "error_message": job.error_message,
    }


@router.post("", response_model=TTSJobResponse, status_code=202)
def create_tts_job(request: TTSCreateRequest, db: Session = Depends(get_db)):
    job = TranslationJob(
        video_id=None,
        job_type="tts",
        parameters=json.dumps({"text": request.text, "voice": request.voice}, ensure_ascii=False),
        status=TranslationJobStatus.QUEUED.value,
        progress=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    synthesize_vietnamese_audio_task.delay(str(job.id))
    return _response(job)


@router.get("/{job_id}", response_model=TTSJobResponse)
def get_tts_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(TranslationJob).filter(
        TranslationJob.id == job_id,
        TranslationJob.job_type == "tts",
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="TTS job not found")
    return _response(job)


@router.get("/{job_id}/audio")
def download_tts_audio(job_id: str, db: Session = Depends(get_db)):
    job = db.query(TranslationJob).filter(
        TranslationJob.id == job_id,
        TranslationJob.job_type == "tts",
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="TTS job not found")
    if job.status != TranslationJobStatus.COMPLETED.value:
        raise HTTPException(status_code=409, detail="TTS audio is not ready")
    if not job.output_file_id:
        raise HTTPException(status_code=404, detail="TTS output file not found")

    file_record = db.query(FileRecord).filter(FileRecord.id == job.output_file_id).first()
    if not file_record or not os.path.isfile(file_record.path):
        raise HTTPException(status_code=404, detail="TTS output file not found")

    return FileResponse(
        path=file_record.path,
        media_type="audio/mpeg",
        filename=f"vietnamese_tts_{job_id}.mp3",
    )