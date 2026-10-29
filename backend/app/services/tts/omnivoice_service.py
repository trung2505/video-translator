"""
OmniVoice TTS Service Implementation

Local neural TTS using k2-fsa/OmniVoice model.
Supports Vietnamese voice and style variants.

Model Info:
- Repository: k2-fsa/OmniVoice
- License: Apache-2.0
- Output: 24kHz WAV
- Device: Automatically selected (CPU/GPU)

Public Interface:
    service = OmniVoiceService()
    wav_path = service.synthesize_vietnamese(text, job_id, voice)
"""

import os
import time
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Global model singleton - loaded once, reused for all requests
_omnivoice_model = None
_model_load_lock = __import__("threading").Lock()


class OmniVoiceError(Exception):
    """OmniVoice-specific errors."""
    pass


class OmniVoiceService:
    """OmniVoice TTS service for Vietnamese text-to-speech."""

    # Voice mapping: voice_name -> OmniVoice instruct parameter
    VOICE_MAPPING = {
        "female_young_adult": "female, young adult",
        "male_young_adult": "male, young adult",
        "female_elderly": "female, elderly",
        "male_deep_voice": "male, very low pitch",
        "female_child": "female, child",
    }

    # OmniVoice model configuration
    MODEL_PATH = "k2-fsa/OmniVoice"
    SAMPLE_RATE = 24000
    NUM_STEPS = 16
    DEVICE = os.getenv("OMNIVOICE_DEVICE", "auto").lower()

    def __init__(self):
        """Initialize OmniVoice service."""
        self.model = None

    @classmethod
    def get_model(cls):
        """
        Lazy-load OmniVoice model as singleton.
        Avoids reloading 3GB model for each request.
        
        Returns:
            OmniVoice model instance
            
        Raises:
            OmniVoiceError: If model loading fails
        """
        global _omnivoice_model

        if _omnivoice_model is not None:
            return _omnivoice_model

        with _model_load_lock:
            # Double-check after acquiring lock
            if _omnivoice_model is not None:
                return _omnivoice_model

            try:
                logger.info(f"Loading OmniVoice model from {cls.MODEL_PATH}...")
                from omnivoice import OmniVoice
                import torch

                if cls.DEVICE not in {"auto", "cpu", "cuda"}:
                    raise OmniVoiceError(
                        "OMNIVOICE_DEVICE must be one of: auto, cpu, cuda"
                    )

                use_cuda = cls.DEVICE == "cuda" or (
                    cls.DEVICE == "auto" and torch.cuda.is_available()
                )
                if cls.DEVICE == "cuda" and not torch.cuda.is_available():
                    raise OmniVoiceError(
                        "OMNIVOICE_DEVICE=cuda requested, but CUDA is unavailable"
                    )

                start = time.time()
                model_kwargs = {"device_map": "cuda"} if use_cuda else {}
                model = OmniVoice.from_pretrained(cls.MODEL_PATH, **model_kwargs)
                elapsed = time.time() - start

                logger.info(
                    f"OmniVoice model loaded on {model.device} in {elapsed:.1f}s"
                )
                _omnivoice_model = model
                return _omnivoice_model

            except ImportError as e:
                raise OmniVoiceError(
                    "OmniVoice package not installed. "
                    "Install with: pip install omnivoice"
                ) from e
            except Exception as e:
                raise OmniVoiceError(
                    f"Failed to load OmniVoice model: {type(e).__name__}: {e}"
                ) from e

    def validate_voice(self, voice: str) -> None:
        """
        Validate voice name.
        
        Args:
            voice: Voice identifier
            
        Raises:
            ValueError: If voice is not in VOICE_MAPPING
        """
        if voice not in self.VOICE_MAPPING:
            valid_voices = ", ".join(sorted(self.VOICE_MAPPING.keys()))
            raise ValueError(
                f"Invalid voice '{voice}'. "
                f"Must be one of: {valid_voices}"
            )

    def validate_text(self, text: str) -> None:
        """
        Validate input text.
        
        Args:
            text: Vietnamese text to synthesize
            
        Raises:
            ValueError: If text is invalid
        """
        if not isinstance(text, str):
            raise ValueError(f"Text must be string, got {type(text).__name__}")

        text_stripped = text.strip()
        if not text_stripped:
            raise ValueError("Text cannot be empty")

    def synthesize_vietnamese(
        self,
        text: str,
        job_id: str,
        voice: str = "female_young_adult",
    ) -> str:
        """
        Synthesize Vietnamese text to speech using OmniVoice.
        
        Args:
            text: Vietnamese text to synthesize
            job_id: Job identifier (used for output filename)
            voice: Voice identifier (default: female_young_adult)
            
        Returns:
            Path to generated WAV file
            
        Raises:
            ValueError: If text or voice is invalid
            OmniVoiceError: If synthesis fails
        """
        # Validation
        self.validate_text(text)
        self.validate_voice(voice)

        # Get instruct parameter for voice
        instruct = self.VOICE_MAPPING[voice]

        try:
            # Load model (singleton, cached)
            model = self.get_model()

            logger.info(
                f"Synthesizing Vietnamese text ({len(text)} chars) "
                f"with voice '{voice}' (job_id: {job_id})"
            )

            start = time.time()

            # OmniVoice inference
            result = model.generate(
                text=text.strip(),
                language="Vietnamese",
                instruct=instruct,
                num_step=self.NUM_STEPS,
            )

            # Handle OmniVoice return type
            # Returns: List[numpy.ndarray] where result[0] is audio
            if isinstance(result, list):
                wav = result[0]
            elif isinstance(result, dict):
                wav = result.get("wav", result)
            else:
                wav = result

            elapsed = time.time() - start

            # Generate output path using job_id
            output_path = self._generate_output_path(job_id, voice)

            # Save to file
            self._save_wav(wav, output_path)

            file_size = os.path.getsize(output_path)
            logger.info(
                f"✅ Synthesis complete in {elapsed:.1f}s "
                f"(saved {file_size:,} bytes to {output_path})"
            )

            return output_path

        except (ValueError, OmniVoiceError):
            # Re-raise validation/model errors
            raise
        except Exception as e:
            raise OmniVoiceError(
                f"Synthesis failed: {type(e).__name__}: {e}"
            ) from e

    def _generate_output_path(self, job_id: str, voice: str) -> str:
        """Generate output path for audio file using job_id."""
        output_dir = Path("/tmp/omnivoice_tts")
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{job_id}_{voice}.wav"
        return str(output_dir / filename)

    def _save_wav(self, wav_data, output_path: str) -> None:
        """Save WAV data to file."""
        try:
            import soundfile as sf
        except ImportError:
            raise OmniVoiceError(
                "soundfile package not installed. "
                "Install with: pip install soundfile"
            )

        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            sf.write(output_path, wav_data, self.SAMPLE_RATE)
        except Exception as e:
            raise OmniVoiceError(
                f"Failed to save WAV file to {output_path}: {e}"
            ) from e
