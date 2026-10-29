import os
import uuid
from pathlib import Path
from app.config import get_settings

settings = get_settings()

class SubtitleService:
    @staticmethod
    def generate_srt(segments: list) -> str:
        """Generate SRT subtitle file from segments"""
        srt_content = ""
        
        for i, segment in enumerate(segments, 1):
            start_time = SubtitleService._format_timestamp(segment["start"])
            end_time = SubtitleService._format_timestamp(segment["end"])
            text = segment.get("translated_text", "")
            
            srt_content += f"{i}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{text}\n\n"
        
        import os
        import uuid
        import textwrap
        import logging
        from typing import List, Dict

        from app.config import get_settings

        settings = get_settings()
        logger = logging.getLogger(__name__)


        DEFAULT_MAX_CHARS_PER_LINE = 42
        DEFAULT_MAX_LINES = 2


        def _format_timestamp(seconds: float) -> str:
            """Format timestamp for SRT (HH:MM:SS,mmm). Clamps negative to 0."""
            if seconds is None or seconds < 0:
                seconds = 0.0
            total_millis = int(round(seconds * 1000))
            millis = total_millis % 1000
            total_seconds = total_millis // 1000
            secs = total_seconds % 60
            minutes = (total_seconds // 60) % 60
            hours = total_seconds // 3600
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


        def _validate_timestamp(start: float, end: float) -> bool:
            try:
                s = float(start)
                e = float(end)
            except Exception:
                return False
            if s < 0 or e <= s:
                return False
            return True


        def _split_text_into_blocks(text: str, max_chars_per_line: int, max_lines: int) -> List[str]:
            """Wrap text into lines and group into blocks (each block has up to max_lines).

            Each block will be joined with newline characters and represent one SRT cue.
            """
            if not text:
                return [""]

            # Use textwrap to break into lines of max_chars_per_line
            wrapped_lines = textwrap.wrap(text, width=max_chars_per_line, break_long_words=True, break_on_hyphens=False)
            if not wrapped_lines:
                return [""]

            blocks: List[str] = []
            for i in range(0, len(wrapped_lines), max_lines):
                block_lines = wrapped_lines[i:i + max_lines]
                blocks.append("\n".join(block_lines))
            return blocks


        class SubtitleService:
            """Service to generate and save SRT subtitle files from translated segments.

            Expected input format: list of dicts with keys: start (float), end (float), translated_text (str)
            Returns path to saved .srt file (UTF-8 encoded).
            """

            @staticmethod
            def generate_srt(segments: List[Dict], max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE, max_lines: int = DEFAULT_MAX_LINES) -> str:
                """Generate SRT content from translated segments.

                - Validates timestamps
                - Splits long subtitle text into multiple cues spread evenly across the original segment duration
                - Preserves UTF-8 Vietnamese characters
                """
                entries: List[str] = []
                counter = 1

                # Sort segments by start time
                segments_sorted = sorted(segments, key=lambda s: float(s.get("start", 0)))

                last_end = 0.0
                for seg in segments_sorted:
                    start = seg.get("start")
                    end = seg.get("end")
                    text = seg.get("translated_text") or seg.get("text") or ""

                    # Validate timestamps
                    try:
                        start_f = float(start)
                        end_f = float(end)
                    except Exception:
                        logger.warning("Skipping segment with invalid timestamps: %s", seg)
                        continue

                    if end_f <= start_f:
                        logger.warning("Skipping segment with non-positive duration: %s", seg)
                        continue

                    # Ensure cues do not overlap previous end
                    if start_f < last_end:
                        start_f = last_end + 0.001
                        if start_f >= end_f:
                            logger.warning("Adjusted start >= end after avoiding overlap, skipping segment: %s", seg)
                            continue

                    # Split text into blocks each containing up to max_lines of wrapped text
                    blocks = _split_text_into_blocks(text, max_chars_per_line, max_lines)

                    # If there are multiple blocks, split time evenly
                    n_blocks = max(1, len(blocks))
                    duration = end_f - start_f
                    # Avoid zero division
                    part_duration = duration / n_blocks if n_blocks > 0 else duration

                    for idx, block in enumerate(blocks):
                        cue_start = start_f + idx * part_duration
                        cue_end = start_f + (idx + 1) * part_duration

                        # Format timestamps
                        start_ts = _format_timestamp(cue_start)
                        end_ts = _format_timestamp(cue_end)

                        # Build SRT entry ensuring UTF-8 content
                        entry = f"{counter}\n{start_ts} --> {end_ts}\n{block}\n"
                        entries.append(entry)
                        counter += 1
                        last_end = cue_end

                return "\n".join(entries)

            @staticmethod
            def save_srt(segments: List[Dict], filename: str = None, max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE, max_lines: int = DEFAULT_MAX_LINES) -> str:
                """Save segments as an SRT file encoded in UTF-8. Returns the path to the file."""
                os.makedirs(settings.PROCESSED_DIR, exist_ok=True)

                if filename:
                    subtitle_path = os.path.join(settings.PROCESSED_DIR, filename)
                else:
                    subtitle_id = str(uuid.uuid4())
                    subtitle_path = os.path.join(settings.PROCESSED_DIR, f"{subtitle_id}.srt")

                srt_content = SubtitleService.generate_srt(segments, max_chars_per_line=max_chars_per_line, max_lines=max_lines)

                try:
                    # Ensure UTF-8 encoding for Vietnamese characters
                    with open(subtitle_path, "w", encoding="utf-8", newline="\n") as f:
                        f.write(srt_content)
                    logger.info("Saved subtitle file: %s", subtitle_path)
                    return subtitle_path
                except Exception:
                    logger.exception("Failed to save subtitle file: %s", subtitle_path)
                    raise
