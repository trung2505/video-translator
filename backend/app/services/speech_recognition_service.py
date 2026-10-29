from faster_whisper import WhisperModel
from app.config import get_settings
import os

settings = get_settings()

# Load model once
model = None

def get_whisper_model():
    global model
    if model is None:
        model = WhisperModel(settings.WHISPER_MODEL, device=settings.WHISPER_DEVICE)
    return model

class SpeechRecognitionService:
    @staticmethod
    def transcribe_audio(audio_path: str, language: str = "zh") -> dict:
        """Transcribe audio to text using Whisper"""
        model = get_whisper_model()
        
        segments, info = model.transcribe(
            audio_path,
            language=language,
            beam_size=5
        )
        
        result = {
            "language": info.language,
            "segments": []
        }
        
        for segment in segments:
            result["segments"].append({
                "id": segment.id,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
        
        return result
    
    @staticmethod
    def detect_language(audio_path: str) -> str:
        """Detect language in audio"""
        model = get_whisper_model()
        
        # Decode audio first
        segments, info = model.transcribe(audio_path, language=None)
        
        return info.language
