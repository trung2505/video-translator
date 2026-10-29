import os
import uuid
from pathlib import Path
import librosa
import soundfile as sf
from app.config import get_settings

settings = get_settings()

class AudioService:
    @staticmethod
    def extract_audio_from_video(video_path: str) -> str:
        """Extract audio from video using FFmpeg"""
        import subprocess
        
        audio_id = str(uuid.uuid4())
        audio_path = os.path.join(settings.PROCESSED_DIR, f"{audio_id}.wav")
        
        os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
        
        # Use FFmpeg to extract audio
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",  # No video
            "-acodec", "pcm_s16le",
            "-ar", "16000",  # 16kHz sample rate
            "-ac", "1",  # Mono
            "-y",  # Overwrite output
            audio_path
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        
        return audio_path
    
    @staticmethod
    def split_audio_chunks(audio_path: str, chunk_duration: int = 30) -> list:
        """Split audio into chunks for processing"""
        y, sr = librosa.load(audio_path, sr=16000)
        
        chunk_samples = chunk_duration * sr
        chunks = []
        
        for i in range(0, len(y), chunk_samples):
            chunk = y[i:i + chunk_samples]
            chunk_id = str(uuid.uuid4())
            chunk_path = os.path.join(settings.PROCESSED_DIR, f"{chunk_id}.wav")
            sf.write(chunk_path, chunk, sr)
            chunks.append({
                "id": chunk_id,
                "path": chunk_path,
                "start_time": i / sr,
                "end_time": min(i + chunk_samples, len(y)) / sr
            })
        
        return chunks
