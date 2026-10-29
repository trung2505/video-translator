from abc import ABC, abstractmethod
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class Transcriber(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> List[Dict]:
        """Transcribe audio and return list of segments with start, end, text."""
        pass


class FasterWhisperTranscriber(Transcriber):
    def __init__(self, model_name: str = "ggml-large.bin", device: str = "cpu"):
        try:
            from faster_whisper import WhisperModel
        except Exception:
            raise RuntimeError("faster-whisper is required for FasterWhisperTranscriber")
        self.model = WhisperModel(model_name, device=device)

    def transcribe(self, audio_path: str) -> List[Dict]:
        segments = []
        try:
            result = self.model.transcribe(audio_path, beam_size=5)
            for segment in result[0]:
                segments.append({
                    "start": float(segment.start),
                    "end": float(segment.end),
                    "text": segment.text.strip()
                })
        except Exception:
            logger.exception("Transcription failed for %s", audio_path)
            raise
        return segments


class DummyTranscriber(Transcriber):
    def transcribe(self, audio_path: str) -> List[Dict]:
        # Development fallback: return empty list
        return []
import os
import subprocess
import uuid
import logging
from typing import List, Dict

from faster_whisper import WhisperModel

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_MODEL: WhisperModel | None = None


def get_whisper_model() -> WhisperModel:
    """Singleton loader for Faster-Whisper model."""
    global _MODEL
    if _MODEL is None:
        try:
            logger.info("Loading Whisper model: %s (device=%s)", settings.WHISPER_MODEL, settings.WHISPER_DEVICE)
            _MODEL = WhisperModel(settings.WHISPER_MODEL, device=settings.WHISPER_DEVICE)
        except Exception:
            logger.exception("Failed to load Whisper model %s", settings.WHISPER_MODEL)
            raise
    return _MODEL


class TranscriptionService:
    """Service to extract audio from video and transcribe Chinese speech using Faster-Whisper.

    Methods
    -------
    transcribe_video(video_path) -> List[Dict]
        Extracts audio and returns list of timestamped segments:
        [{"start": 0.0, "end": 2.3, "text": "你好"}, ...]
    """

    @staticmethod
    def _extract_audio(video_path: str) -> str:
        """Extract audio from a video file to a WAV file (16kHz mono) using ffmpeg.

        Returns the path to the temporary WAV file.
        Raises subprocess.CalledProcessError if ffmpeg fails.
        """
        os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
        audio_id = str(uuid.uuid4())
        audio_path = os.path.join(settings.PROCESSED_DIR, f"{audio_id}.wav")

        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            "-y",
            audio_path,
        ]

        try:
            logger.info("Extracting audio from %s to %s", video_path, audio_path)
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info("Audio extracted: %s", audio_path)
            return audio_path
        except subprocess.CalledProcessError as e:
            logger.exception("FFmpeg error extracting audio from %s: %s", video_path, e)
            # Clean up partial file if exists
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
            except Exception:
                logger.warning("Could not remove partial audio file %s", audio_path)
            raise

    @staticmethod
    def transcribe_video(video_path: str, force_language: str = "zh") -> List[Dict]:
        """Transcribe the given video file and return timestamped segments.

        - Extracts audio with FFmpeg
        - Uses Faster-Whisper to transcribe
        - Detects language reported by the model and logs if it's not Chinese

        Returns:
            List[Dict]: [{"start": float, "end": float, "text": str}, ...]

        Raises exceptions on failure (ffmpeg/model errors).
        """
        audio_path = None
        try:
            model = get_whisper_model()

            # 1) extract audio
            audio_path = TranscriptionService._extract_audio(video_path)

            # 2) transcribe (force language to Chinese to bias model)
            logger.info("Starting transcription for %s", audio_path)
            segments, info = model.transcribe(audio_path, language=force_language, beam_size=5)

            detected_lang = getattr(info, "language", None)
            logger.info("Whisper detected language: %s", detected_lang)
            if detected_lang and not str(detected_lang).lower().startswith("zh"):
                logger.warning("Detected language is not Chinese: %s", detected_lang)

            results: List[Dict] = []
            for seg in segments:
                try:
                    start = float(seg.start)
                    end = float(seg.end)
                    text = str(seg.text).strip()
                except Exception:
                    logger.exception("Invalid segment format: %s", seg)
                    continue

                # Keep segments only if they contain text
                if text:
                    results.append({"start": start, "end": end, "text": text})

            logger.info("Transcription finished for %s, %d segments", video_path, len(results))
            return results

        except Exception:
            logger.exception("Transcription pipeline failed for %s", video_path)
            raise

        finally:
            # cleanup temporary audio file
            if audio_path:
                try:
                    os.remove(audio_path)
                    logger.debug("Removed temp audio file %s", audio_path)
                except Exception:
                    logger.warning("Failed to remove temp audio file %s", audio_path)
