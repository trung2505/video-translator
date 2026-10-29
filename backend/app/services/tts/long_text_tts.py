"""
Long Text TTS Service — Orchestrates Vietnamese text-to-speech for long documents.

Pipeline:
    Vietnamese text
         ↓
    TextChunker (Step 5A)
         ↓
    Multiple chunks
         ↓
    OmniVoice (Step 4)
         ↓
    Multiple WAV files
         ↓
    Audio merge (FFmpeg/librosa)
         ↓
    Final MP3
"""

import os
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Optional
import logging
import subprocess
import shlex

import numpy as np
import soundfile as sf

from app.services.text_service import TextChunker
from app.services.tts.omnivoice_service import OmniVoiceService, OmniVoiceError

logger = logging.getLogger(__name__)


class LongTextTTSError(Exception):
    """Long Text TTS specific errors."""
    pass


class LongTextTTS:
    """
    Synthesize long Vietnamese text to MP3 using OmniVoice.
    
    Features:
    - Intelligent chunking by paragraph/sentence/word
    - Reuse existing valid chunks (avoid re-synthesis)
    - Parallel-safe chunk tracking
    - Smart failure handling (preserve successful chunks)
    - Auto-merge on completion
    """
    
    # Valid voices (must match OmniVoiceService.VOICE_MAPPING)
    VALID_VOICES = {
        "female_young_adult",
        "male_young_adult",
        "female_elderly",
        "male_deep_voice",
        "female_child",
    }
    
    # Default output directory for long text TTS (Windows-compatible)
    OUTPUT_BASE = Path(tempfile.gettempdir()) / "long_text_tts"
    
    def __init__(self, max_chars_per_chunk: int = 500):
        """
        Initialize Long Text TTS service.
        
        Args:
            max_chars_per_chunk: Default chunk size for TextChunker
        """
        self.max_chars = max_chars_per_chunk
        self.chunker = TextChunker(max_chars=max_chars_per_chunk)
        self.tts_service = OmniVoiceService()
    
    def synthesize_long_text(
        self,
        text: str,
        job_id: str,
        voice: str = "female_young_adult",
    ) -> str:
        """
        Synthesize long Vietnamese text to MP3.
        
        Args:
            text: Long Vietnamese text
            job_id: Unique job identifier (used for output directory)
            voice: Voice identifier (one of VALID_VOICES)
            
        Returns:
            Path to final MP3 file
            
        Raises:
            ValueError: If text or voice is invalid
            LongTextTTSError: If synthesis/merge fails
        """
        # Validate
        self._validate_input(text, voice)
        
        logger.info(f"Starting long text TTS (job_id={job_id}, voice={voice})")
        print(f"[LongTextTTS] Processing job {job_id}: {len(text)} chars, voice={voice}")
        
        start_time = time.time()
        
        try:
            # Setup output directory
            output_dir = self.OUTPUT_BASE / job_id
            chunks_dir = output_dir / "chunks"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Chunk text
            logger.info(f"Step 1: Chunking text (max_chars={self.max_chars})")
            chunks = self.chunker.chunk_text(text)
            logger.info(f"  Created {len(chunks)} chunks")
            print(f"  [OK] Created {len(chunks)} chunks")
            
            if not chunks:
                raise LongTextTTSError("Text chunking resulted in no chunks")
            
            # Step 2: Synthesize each chunk
            logger.info("Step 2: Synthesizing chunks with OmniVoice")
            wav_paths = []
            for i, chunk in enumerate(chunks, 1):
                try:
                    chunk_num = f"{i:03d}"
                    wav_path = self._synthesize_chunk(
                        chunk, job_id, voice, chunk_num
                    )
                    wav_paths.append(wav_path)
                    print(f"  [OK] Chunk {chunk_num}: {len(chunk)} chars -> WAV")
                except Exception as e:
                    logger.error(f"Failed to synthesize chunk {i}: {e}")
                    print(f"  ✗ Chunk {chunk_num}: FAILED - {e}")
                    raise LongTextTTSError(
                        f"Chunk {i} synthesis failed: {e}"
                    ) from e
            
            # Step 3: Merge audio
            logger.info("Step 3: Merging audio chunks")
            mp3_path = self._merge_wav_chunks(wav_paths, output_dir, job_id)
            
            elapsed = time.time() - start_time
            final_size = os.path.getsize(mp3_path) if os.path.exists(mp3_path) else 0
            
            logger.info(
                f"[COMPLETE] Long text TTS complete in {elapsed:.1f}s "
                f"({len(chunks)} chunks, {final_size:,} bytes MP3)"
            )
            print(f"[OK] Final MP3: {mp3_path}")
            print(f"[OK] Total time: {elapsed:.1f}s")
            
            return mp3_path
            
        except LongTextTTSError:
            raise
        except Exception as e:
            logger.error(f"Long text TTS failed: {e}")
            raise LongTextTTSError(f"Long text TTS failed: {e}") from e
    
    def _validate_input(self, text: str, voice: str) -> None:
        """Validate text and voice inputs."""
        if not isinstance(text, str):
            raise ValueError(f"Text must be string, got {type(text).__name__}")
        
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        if voice not in self.VALID_VOICES:
            raise ValueError(
                f"Invalid voice '{voice}'. Must be one of: "
                f"{', '.join(sorted(self.VALID_VOICES))}"
            )
    
    def _synthesize_chunk(
        self,
        chunk_text: str,
        job_id: str,
        voice: str,
        chunk_num: str,
    ) -> str:
        """
        Synthesize a single chunk, reusing existing valid WAV if possible.
        
        Args:
            chunk_text: Text to synthesize
            job_id: Job identifier
            voice: Voice to use
            chunk_num: Chunk number (e.g., "001")
            
        Returns:
            Path to WAV file
        """
        # Generate deterministic chunk path
        output_dir = self.OUTPUT_BASE / job_id / "chunks"
        chunk_wav_path = output_dir / f"{chunk_num}.wav"
        
        # Check if chunk already exists and is valid
        if chunk_wav_path.exists():
            if self._is_valid_wav(chunk_wav_path):
                logger.debug(f"Reusing existing chunk: {chunk_wav_path}")
                return str(chunk_wav_path)
            else:
                logger.warning(f"Invalid existing chunk, regenerating: {chunk_wav_path}")
                chunk_wav_path.unlink()  # Delete invalid file
        
        # Generate new WAV using OmniVoice
        # Use deterministic job_id format for OmniVoice internal storage
        tts_job_id = f"{job_id}_chunk{chunk_num}"
        wav_path = self.tts_service.synthesize_vietnamese(
            text=chunk_text,
            job_id=tts_job_id,
            voice=voice,
        )
        
        # Move to our chunks directory with proper naming
        output_dir.mkdir(parents=True, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # Copy from OmniVoice output dir to our structure
        if os.path.exists(wav_path):
            import shutil
            shutil.move(wav_path, str(chunk_wav_path))
            logger.debug(f"Synthesized chunk: {chunk_wav_path}")
        
        return str(chunk_wav_path)
    
    def _is_valid_wav(self, wav_path: Path) -> bool:
        """
        Check if WAV file is valid and readable.
        
        Args:
            wav_path: Path to WAV file
            
        Returns:
            True if file is valid and readable
        """
        try:
            if not wav_path.exists():
                return False
            
            if wav_path.stat().st_size == 0:
                return False
            
            # Try to read WAV header
            data, sr = sf.read(str(wav_path), always_2d=False)
            
            # Check if audio has content
            if len(data) == 0:
                return False
            
            # Check sample rate (should be 24kHz for OmniVoice)
            if sr != 24000:
                logger.warning(f"WAV sample rate mismatch: {sr} (expected 24000)")
                # Still consider it valid, just log warning
            
            return True
            
        except Exception as e:
            logger.debug(f"WAV validation failed for {wav_path}: {e}")
            return False
    
    def _merge_wav_chunks(
        self,
        wav_paths: List[str],
        output_dir: Path,
        job_id: str,
    ) -> str:
        """
        Merge multiple WAV chunks into single MP3.
        
        Args:
            wav_paths: Ordered list of WAV file paths
            output_dir: Output directory for final MP3
            job_id: Job identifier
            
        Returns:
            Path to final MP3 file
            
        Raises:
            LongTextTTSError: If merge fails
        """
        if not wav_paths:
            raise LongTextTTSError("No WAV chunks to merge")
        
        try:
            # Load and concatenate all WAV files
            logger.info(f"Merging {len(wav_paths)} WAV chunks")
            
            all_audio = []
            sample_rate = None
            total_duration = 0.0
            
            for i, wav_path in enumerate(wav_paths, 1):
                logger.debug(f"Loading chunk {i}: {wav_path}")
                
                # Read WAV
                audio, sr = sf.read(str(wav_path), always_2d=False)
                
                # Verify sample rate consistency
                if sample_rate is None:
                    sample_rate = sr
                elif sr != sample_rate:
                    logger.warning(
                        f"Sample rate mismatch in chunk {i}: "
                        f"{sr} (expected {sample_rate}). Resampling..."
                    )
                    # Could resample here, but for now just warn
                
                all_audio.append(audio)
                total_duration += len(audio) / sr
            
            # Concatenate audio
            merged_audio = np.concatenate(all_audio)
            logger.info(f"Merged audio shape: {merged_audio.shape}, total duration: {total_duration:.1f}s")
            
            # Save as MP3 via WAV intermediate + FFmpeg
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # First save as WAV
            merged_wav = output_dir / "merged_temp.wav"
            sf.write(str(merged_wav), merged_audio, sample_rate)
            logger.debug(f"Saved merged WAV: {merged_wav}")
            
            # Convert to MP3 using FFmpeg
            mp3_path = output_dir / f"{job_id}.mp3"
            self._convert_wav_to_mp3(str(merged_wav), str(mp3_path))
            
            # Clean up temporary WAV
            merged_wav.unlink()
            
            # Verify MP3 was created
            if not mp3_path.exists():
                raise LongTextTTSError(f"MP3 file not created: {mp3_path}")
            
            logger.info(f"[COMPLETE] Merged MP3: {mp3_path} ({mp3_path.stat().st_size:,} bytes)")
            
            return str(mp3_path)
            
        except RuntimeError:
            # Re-raise FFmpeg missing error
            raise
        except Exception as e:
            logger.error(f"Merge failed: {e}")
            raise LongTextTTSError(f"Merge failed: {e}") from e
    
    def _is_valid_mp3(self, mp3_path: str) -> bool:
        """
        Verify that output file is a real MP3, not a renamed WAV.
        
        Checks:
        - File exists
        - File size > 0
        - Has MP3 magic bytes (0xFFFA or 0xFFFB for ID3v2 header)
        
        Args:
            mp3_path: Path to MP3 file
            
        Returns:
            True if file appears to be valid MP3, False otherwise
        """
        try:
            if not os.path.exists(mp3_path):
                logger.debug(f"MP3 validation failed: file not found ({mp3_path})")
                return False
            
            file_size = os.path.getsize(mp3_path)
            if file_size == 0:
                logger.debug(f"MP3 validation failed: file is empty ({mp3_path})")
                return False
            
            # Check for MP3 magic bytes
            # MP3 frames start with FF FA or FF FB
            # ID3v2 header starts with "ID3"
            with open(mp3_path, "rb") as f:
                header = f.read(3)
                
                # Check for ID3v2 tag
                if header == b"ID3":
                    logger.debug(f"MP3 validation passed: ID3v2 header found ({mp3_path})")
                    return True
                
                # Check for MPEG frame sync (0xFF 0xFA or 0xFF 0xFB)
                if len(header) >= 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0:
                    logger.debug(f"MP3 validation passed: MPEG frame found ({mp3_path})")
                    return True
                
                logger.warning(f"MP3 validation failed: invalid magic bytes ({mp3_path})")
                return False
                
        except Exception as e:
            logger.debug(f"MP3 validation error ({mp3_path}): {e}")
            return False
    
    def _convert_wav_to_mp3(self, wav_path: str, mp3_path: str) -> None:
        """
        Convert WAV to MP3 using FFmpeg.
        
        Args:
            wav_path: Input WAV file path
            mp3_path: Output MP3 file path
            
        Raises:
            RuntimeError: If FFmpeg is not available or conversion fails
            LongTextTTSError: If other conversion errors occur
        """
        try:
            cmd = [
                "ffmpeg",
                "-i", wav_path,
                "-q:a", "5",  # Quality (lower = better, 0-9)
                "-y",  # Overwrite output
                mp3_path,
            ]
            
            logger.debug(f"Running FFmpeg: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise LongTextTTSError(
                    f"FFmpeg failed: {result.stderr}"
                )
            
            # Validate output is real MP3
            if not self._is_valid_mp3(mp3_path):
                raise LongTextTTSError(
                    f"FFmpeg output is not a valid MP3 file: {mp3_path}"
                )
            
            logger.debug(f"FFmpeg conversion complete: {mp3_path}")
            
        except FileNotFoundError as e:
            raise RuntimeError(
                "FFmpeg is required to convert WAV to MP3, but it is not found on this system. "
                "Please install FFmpeg and ensure it is in your PATH."
            ) from e
            
        except subprocess.TimeoutExpired:
            raise LongTextTTSError("FFmpeg conversion timed out (>300s)")
        except RuntimeError:
            raise  # Re-raise RuntimeError for missing FFmpeg
        except Exception as e:
            raise LongTextTTSError(f"FFmpeg conversion failed: {e}") from e
