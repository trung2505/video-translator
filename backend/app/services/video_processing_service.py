import subprocess
import os
import uuid
from pathlib import Path
from app.config import get_settings

settings = get_settings()

class VideoProcessingService:
    @staticmethod
    def burn_subtitles_to_video(video_path: str, subtitle_path: str) -> str:
        """Burn subtitles into video using FFmpeg"""
        output_id = str(uuid.uuid4())
        output_path = os.path.join(settings.PROCESSED_DIR, f"{output_id}_translated.mp4")
        
        os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
        
        # FFmpeg command to burn subtitles
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"subtitles={subtitle_path}:force_style='FontSize=24'",
            "-c:a", "aac",
            "-y",
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        
        return output_path
    
    @staticmethod
    def get_video_duration(video_path: str) -> float:
        """Get video duration in seconds"""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1:nokey=1",
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
