import subprocess
import shlex
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class FFmpegService:
    @staticmethod
    def get_video_duration(video_path: str) -> float:
        """Return duration in seconds using ffprobe."""
        cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {shlex.quote(video_path)}"
        try:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            return float(out.strip())
        except subprocess.CalledProcessError as exc:
            logger.error("ffprobe failed: %s", exc.output.decode(errors='ignore') if exc.output else exc)
            raise

    @staticmethod
    def extract_audio(video_path: str, out_path: Optional[str] = None) -> str:
        """Extract audio to WAV 16k mono for transcription.

        Returns path to extracted audio file.
        """
        video = Path(video_path)
        if not out_path:
            out_path = str(video.with_suffix('.wav'))

        cmd = [
            'ffmpeg', '-y', '-i', str(video_path), '-vn', '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', out_path
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return out_path
        except subprocess.CalledProcessError as exc:
            logger.error('FFmpeg extract_audio failed: %s', exc.stderr.decode(errors='ignore'))
            raise

    @staticmethod
    def burn_subtitles(video_path: str, subtitle_path: str, out_path: Optional[str] = None, crf: int = 18, preset: str = 'veryfast') -> str:
        video = Path(video_path)
        if not out_path:
            out_path = str(video.with_name(video.stem + '_subt.mp4'))

        # Escape subtitle path for ffmpeg subtitles filter
        s = str(Path(subtitle_path).resolve())
        s_escaped = s.replace("'", "\\'").replace('\\', '\\\\')
        subtitles_filter = f"subtitles='{s_escaped}':charenc=UTF-8"

        cmd = [
            'ffmpeg', '-y', '-i', str(video_path), '-vf', subtitles_filter, '-c:v', 'libx264', '-crf', str(crf), '-preset', preset, '-c:a', 'copy', out_path
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return out_path
        except subprocess.CalledProcessError as exc:
            logger.error('FFmpeg burn_subtitles failed: %s', exc.stderr.decode(errors='ignore'))
            raise
