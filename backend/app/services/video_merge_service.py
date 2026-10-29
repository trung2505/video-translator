import logging
import subprocess
from pathlib import Path
from typing import Optional

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class VideoMergeService:
    """Service to burn (render) SRT subtitles into a video using FFmpeg.

    - Preserves original resolution by not applying any scaling.
    - Preserves original audio (`-c:a copy`).
    - Exports an MP4 file (H.264 video, AAC passthrough for audio if copy not supported).
    """

    @staticmethod
    def _escape_subtitle_path_for_filter(path: Path) -> str:
        # FFmpeg subtitles filter expects special escaping for Windows paths.
        # Replace backslashes with double backslashes and escape single quotes.
        s = str(path)
        s = s.replace("'", "\\'")
        s = s.replace("\\", "\\\\")
        return s

    @staticmethod
    def burn_subtitles(
        video_path: str,
        subtitle_path: str,
        output_dir: Optional[str] = None,
        output_filename: Optional[str] = None,
        crf: int = 18,
        preset: str = "veryfast",
    ) -> str:
        """Burn `subtitle_path` (SRT) into `video_path` and return output MP4 path.

        Raises subprocess.CalledProcessError on failure.
        """
        vpath = Path(video_path)
        spath = Path(subtitle_path)

        if not vpath.exists():
            raise FileNotFoundError(f"Input video not found: {vpath}")
        if not spath.exists():
            raise FileNotFoundError(f"Subtitle file not found: {spath}")

        out_dir = Path(output_dir) if output_dir else Path(settings.PROCESSED_DIR)
        out_dir.mkdir(parents=True, exist_ok=True)

        if output_filename:
            out_path = out_dir / output_filename
        else:
            stem = vpath.stem
            out_path = out_dir / f"{stem}_subt.mp4"

        # Build the subtitles filter string with proper escaping
        filter_path = VideoMergeService._escape_subtitle_path_for_filter(spath.resolve())
        subtitles_filter = f"subtitles='{filter_path}':charenc=UTF-8"

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(vpath.resolve()),
            "-vf",
            subtitles_filter,
            "-c:v",
            "libx264",
            "-crf",
            str(crf),
            "-preset",
            preset,
            "-c:a",
            "copy",
            str(out_path.resolve()),
        ]

        logger.info("Running ffmpeg to burn subtitles: %s", " ".join(cmd))

        try:
            completed = subprocess.run(cmd, check=True, capture_output=True)
            logger.debug("ffmpeg stdout: %s", completed.stdout.decode(errors="ignore"))
            logger.debug("ffmpeg stderr: %s", completed.stderr.decode(errors="ignore"))
        except subprocess.CalledProcessError as exc:
            # Log ffmpeg output for debugging then re-raise
            out = exc.stdout.decode(errors="ignore") if exc.stdout else ""
            err = exc.stderr.decode(errors="ignore") if exc.stderr else ""
            logger.error("FFmpeg failed. stdout=%s stderr=%s", out, err)
            raise

        return str(out_path.resolve())
