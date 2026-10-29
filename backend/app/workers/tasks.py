from app.workers.celery_app import celery_app
from celery.utils.log import get_task_logger
from app.db.session import SessionLocal
from app import models
from app.core.config import get_settings
from app.services.storage_service import LocalStorage
from app.services.ffmpeg_service import FFmpegService
from app.services.transcription_service import FasterWhisperTranscriber, DummyTranscriber
from app.services.translation_service import GeminiTranslator, DummyTranslator
from app.services.subtitle_service import SubtitleService
from app.services.video_merge_service import VideoMergeService
from app.services.tts.long_text_tts import LongTextTTS, LongTextTTSError
from datetime import datetime
import json
import traceback

logger = get_task_logger(__name__)
settings = get_settings()


@celery_app.task(bind=True)
def extract_audio_task(self, job_id: str, video_id: str, original_path: str):
    """Extract audio from video. First task in pipeline - sets task_id and started_at."""
    db = SessionLocal()
    storage = LocalStorage()
    try:
        job = db.query(models.TranslationJob).filter(models.TranslationJob.id == job_id).first()
        video = db.query(models.Video).filter(models.Video.id == video_id).first()
        if not job or not video:
            logger.error("Job or Video not found: %s %s", job_id, video_id)
            return

        # First task - set task_id, status, and started_at
        job.task_id = self.request.id  # Celery task ID
        job.status = models.TranslationJobStatus.RUNNING.value
        job.started_at = datetime.utcnow()
        job.progress = 5
        db.commit()
        logger.info(f"Job {job_id} started (task_id={self.request.id})")

        audio_path = FFmpegService.extract_audio(original_path)

        # enqueue next
        transcribe_task.delay(str(job.id), str(audio_path))
        return {"audio_path": audio_path}
    except Exception as exc:
        db.rollback()
        job = db.query(models.TranslationJob).filter(models.TranslationJob.id == job_id).first()
        if job:
            job.status = models.TranslationJobStatus.FAILED.value
            job.error_message = str(exc)
            job.finished_at = datetime.utcnow()
            db.add(job)
            db.commit()
        logger.error("extract_audio_task failed: %s", traceback.format_exc())
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def transcribe_task(self, job_id: str, audio_path: str):
    db = SessionLocal()
    try:
        job = db.query(models.TranslationJob).filter(models.TranslationJob.id == job_id).first()
        video = db.query(models.Video).filter(models.Video.id == job.video_id).first()
        # Continue processing - job already has task_id and started_at from extract_audio_task
        job.status = models.TranslationJobStatus.RUNNING.value
        job.progress = 20
        db.commit()

        # instantiate transcriber (use Dummy if faster-whisper unavailable)
        try:
            transcriber = FasterWhisperTranscriber()
        except Exception:
            transcriber = DummyTranscriber()

        segments = transcriber.transcribe(audio_path)

        # persist segments
        for idx, s in enumerate(segments):
            seg = models.Segment(job_id=job.id, start=s.get('start'), end=s.get('end'), original_text=s.get('text'), order_index=idx)
            db.add(seg)
        db.commit()

        # enqueue translate
        translate_task.delay(str(job.id))
        return {"segments_count": len(segments)}
    except Exception as exc:
        db.rollback()
        job = db.query(models.TranslationJob).filter(models.TranslationJob.id == job_id).first()
        if job:
            job.status = models.TranslationJobStatus.FAILED.value
            job.error_message = str(exc)
            job.finished_at = datetime.utcnow()
            db.add(job)
            db.commit()
        logger.error("transcribe_task failed: %s", traceback.format_exc())
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def translate_task(self, job_id: str):
    db = SessionLocal()
    try:
        job = db.query(models.TranslationJob).filter(models.TranslationJob.id == job_id).first()
        job.status = models.TranslationJobStatus.RUNNING.value
        job.progress = 50
        db.commit()

        # load segments
        segments = db.query(models.Segment).filter(models.Segment.job_id == job.id).order_by(models.Segment.order_index).all()
        texts = [s.original_text or "" for s in segments]

        try:
            translator = GeminiTranslator()
        except Exception:
            translator = DummyTranslator()

        translated = translator.translate(texts)

        for seg, ttext in zip(segments, translated):
            seg.translated_text = ttext
            db.add(seg)
        db.commit()

        # Chain to subtitle generation
        subtitle_task.delay(str(job.id))
        return {"translated_count": len(translated)}
    except Exception as exc:
        db.rollback()
        job = db.query(models.TranslationJob).filter(models.TranslationJob.id == job_id).first()
        if job:
            job.status = models.TranslationJobStatus.FAILED.value
            job.error_message = str(exc)
            job.finished_at = datetime.utcnow()
            db.add(job)
            db.commit()
        logger.error("translate_task failed: %s", traceback.format_exc())
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def synthesize_vietnamese_audio_task(self, job_id: str):
    """
    Synthesize Vietnamese audio from translated text.
    
    Uses LongTextTTS to generate Vietnamese speech from translated segments.
    Pipeline: Vietnamese text → TextChunker → OmniVoice → WAV concatenation → FFmpeg → MP3
    
    Input: All segments must have translated_text (populated by translate_task)
    Output: MP3 file stored as FileRecord, job.output_file_id updated
    The TTS workflow ends after the MP3 is stored and the job is completed.
    """
    db = SessionLocal()
    storage = LocalStorage()
    try:
        job = db.query(models.TranslationJob).filter(models.TranslationJob.id == job_id).first()
        if not job:
            raise LongTextTTSError(f"Translation job not found: {job_id}")

        if job.task_id is None:
            job.task_id = self.request.id
        if job.started_at is None:
            job.started_at = datetime.utcnow()
        job.status = models.TranslationJobStatus.RUNNING.value
        job.progress = 10
        db.commit()

        parameters = {}
        if job.parameters:
            try:
                parameters = json.loads(job.parameters)
            except (TypeError, json.JSONDecodeError) as exc:
                raise LongTextTTSError("Invalid TTS job parameters") from exc
            if not isinstance(parameters, dict):
                raise LongTextTTSError("TTS job parameters must be a JSON object")

        if job.job_type == "tts":
            vietnamese_text = parameters.get("text", "")
        else:
            # Existing video jobs continue to read translated Segment rows.
            segments = db.query(models.Segment).filter(models.Segment.job_id == job.id).order_by(models.Segment.order_index).all()
            vietnamese_texts = [s.translated_text or "" for s in segments]
            vietnamese_text = "\n".join(vietnamese_texts)
        
        if not vietnamese_text.strip():
            raise LongTextTTSError("No Vietnamese text available for TTS synthesis")
        
        logger.info(f"Synthesizing Vietnamese audio (job_id={job_id}, text_length={len(vietnamese_text)})")
        
        # Keep the default for existing jobs while allowing the existing
        # parameters JSON field to select any LongTextTTS-supported voice.
        voice = parameters.get("voice", "female_young_adult")
        
        # Synthesize using LongTextTTS
        tts_service = LongTextTTS()
        mp3_path = tts_service.synthesize_long_text(
            text=vietnamese_text,
            job_id=str(job.id),
            voice=voice
        )
        
        logger.info(f"Vietnamese audio synthesis complete: {mp3_path}")
        
        saved_mp3_path = storage.save_processed_file(
            mp3_path,
            dest_filename=f"{job.id}.mp3",
        )

        # Create FileRecord for the MP3
        fr = models.FileRecord(file_type='tts_audio', path=saved_mp3_path)
        db.add(fr)
        db.commit()
        db.refresh(fr)
        
        # Update job output file reference
        job.output_file_id = fr.id
        job.status = models.TranslationJobStatus.COMPLETED.value
        job.progress = 100
        job.finished_at = datetime.utcnow()
        db.add(job)
        db.commit()

        return {"mp3_path": saved_mp3_path, "file_id": str(fr.id)}
        
    except LongTextTTSError as exc:
        db.rollback()
        job = db.query(models.TranslationJob).filter(models.TranslationJob.id == job_id).first()
        if job:
            job.status = models.TranslationJobStatus.FAILED.value
            job.error_message = f"TTS synthesis failed: {str(exc)}"
            job.finished_at = datetime.utcnow()
            db.add(job)
            db.commit()
        logger.error("synthesize_vietnamese_audio_task failed: %s", traceback.format_exc())
        raise
    except Exception as exc:
        db.rollback()
        job = db.query(models.TranslationJob).filter(models.TranslationJob.id == job_id).first()
        if job:
            job.status = models.TranslationJobStatus.FAILED.value
            job.error_message = f"Vietnamese audio synthesis failed: {str(exc)}"
            job.finished_at = datetime.utcnow()
            db.add(job)
            db.commit()
        logger.error("synthesize_vietnamese_audio_task failed: %s", traceback.format_exc())
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def subtitle_task(self, job_id: str):
    db = SessionLocal()
    storage = LocalStorage()
    try:
        job = db.query(models.TranslationJob).filter(models.TranslationJob.id == job_id).first()
        job.status = models.TranslationJobStatus.RUNNING.value
        job.progress = 75
        db.commit()

        segments = db.query(models.Segment).filter(models.Segment.job_id == job.id).order_by(models.Segment.order_index).all()
        segs = [{"start": s.start, "end": s.end, "text": s.translated_text or s.original_text} for s in segments]

        srt_content = SubtitleService.generate_srt(segs)

        # save srt to processed dir
        import tempfile
        fd, tmp_path = tempfile.mkstemp(suffix='.srt')
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)

        saved = storage.save_processed_file(tmp_path, dest_filename=f"{job.id}.srt")

        # create FileRecord
        fr = models.FileRecord(file_type='subtitle', path=saved)
        db.add(fr)
        db.commit()
        db.refresh(fr)

        # update video
        video = db.query(models.Video).filter(models.Video.id == job.video_id).first()
        video.subtitle_file_id = fr.id
        db.add(video)
        db.commit()

        burn_task.delay(str(job.id))
        return {"srt_path": saved}
    except Exception as exc:
        db.rollback()
        job = db.query(models.TranslationJob).filter(models.TranslationJob.id == job_id).first()
        if job:
            job.status = models.TranslationJobStatus.FAILED.value
            job.error_message = str(exc)
            job.finished_at = datetime.utcnow()
            db.add(job)
            db.commit()
        logger.error("subtitle_task failed: %s", traceback.format_exc())
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def burn_task(self, job_id: str):
    """Final task in pipeline - sets finished_at on completion."""
    db = SessionLocal()
    storage = LocalStorage()
    try:
        job = db.query(models.TranslationJob).filter(models.TranslationJob.id == job_id).first()
        job.status = models.TranslationJobStatus.RUNNING.value
        job.progress = 90
        db.commit()

        video = db.query(models.Video).filter(models.Video.id == job.video_id).first()
        original = video.original_file.path
        subtitle = db.query(models.FileRecord).filter(models.FileRecord.id == video.subtitle_file_id).first().path

        out_path = VideoMergeService.burn_subtitles(original, subtitle)

        saved = storage.save_processed_file(out_path, dest_filename=f"{video.id}_translated.mp4")

        fr = models.FileRecord(file_type='video_processed', path=saved)
        db.add(fr)
        db.commit()
        db.refresh(fr)

        video.processed_file_id = fr.id
        video.status = "completed"
        video.progress = 100
        db.add(video)

        job.status = models.TranslationJobStatus.COMPLETED.value
        job.finished_at = datetime.utcnow()  # Final task - mark as finished
        job.progress = 100
        db.add(job)
        db.commit()
        logger.info(f"Job {job_id} completed")

        return {"processed_path": saved}
    except Exception as exc:
        db.rollback()
        job = db.query(models.TranslationJob).filter(models.TranslationJob.id == job_id).first()
        if job:
            job.status = models.TranslationJobStatus.FAILED.value
            job.error_message = str(exc)
            job.finished_at = datetime.utcnow()  # Mark as finished even on failure
            db.add(job)
            db.commit()
        logger.error("burn_task failed: %s", traceback.format_exc())
        raise
    finally:
        db.close()
from celery import Celery
from app.config import get_settings
from app.services.audio_service import AudioService
from app.services.speech_recognition_service import SpeechRecognitionService
from app.services.translation_service import TranslationService
from app.services.subtitle_service import SubtitleService
from app.services.video_processing_service import VideoProcessingService
from app.models import TranslationJob, TranslationJobStatus
from app.database import SessionLocal
import traceback

settings = get_settings()

celery_app = Celery(
    "video_translator",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

@celery_app.task(bind=True)
def process_video_translation(self, job_id: str, video_id: str, video_path: str):
    """Main task for video translation pipeline"""
    db = SessionLocal()
    job = db.query(TranslationJob).filter(TranslationJob.id == job_id).first()
    
    try:
        # Update status
        job.status = TranslationStatus.processing
        db.commit()
        
        # Step 1: Extract audio (20%)
        self.update_state(state='PROGRESS', meta={'progress': 5})
        job.progress = 5
        db.commit()
        
        audio_path = AudioService.extract_audio_from_video(video_path)
        
        self.update_state(state='PROGRESS', meta={'progress': 20})
        job.progress = 20
        db.commit()
        
        # Step 2: Detect language and transcribe (40%)
        self.update_state(state='PROGRESS', meta={'progress': 25})
        job.progress = 25
        db.commit()
        
        transcription_result = SpeechRecognitionService.transcribe_audio(audio_path)
        job.transcription = str(transcription_result)
        
        self.update_state(state='PROGRESS', meta={'progress': 40})
        job.progress = 40
        db.commit()
        
        # Step 3: Translate text (60%)
        self.update_state(state='PROGRESS', meta={'progress': 45})
        job.progress = 45
        db.commit()
        
        translated_segments = TranslationService.translate_segments(
            transcription_result["segments"],
            source_lang="zh",
            target_lang="vi"
        )
        job.translation = str(translated_segments)
        
        self.update_state(state='PROGRESS', meta={'progress': 60})
        job.progress = 60
        db.commit()
        
        # Step 4: Generate subtitles (80%)
        self.update_state(state='PROGRESS', meta={'progress': 65})
        job.progress = 65
        db.commit()
        
        subtitle_path = SubtitleService.save_srt(translated_segments)
        job.subtitles_path = subtitle_path
        
        self.update_state(state='PROGRESS', meta={'progress': 80})
        job.progress = 80
        db.commit()
        
        # Step 5: Burn subtitles to video (100%)
        self.update_state(state='PROGRESS', meta={'progress': 85})
        job.progress = 85
        db.commit()
        
        output_video_path = VideoProcessingService.burn_subtitles_to_video(video_path, subtitle_path)
        job.output_video_path = output_video_path
        
        self.update_state(state='PROGRESS', meta={'progress': 100})
        job.progress = 100
        job.status = TranslationStatus.completed
        db.commit()
        
    except Exception as e:
        job.status = TranslationStatus.failed
        job.error_message = str(e) + "\n" + traceback.format_exc()
        db.commit()
        raise
    finally:
        db.close()
