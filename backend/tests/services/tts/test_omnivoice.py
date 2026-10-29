"""
Tests for OmniVoice TTS Service

Tests cover public API: synthesize_vietnamese(text, job_id, voice)
Unit tests use mocking; integration test uses real model.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import tempfile
import os

from app.services.tts.omnivoice_service import OmniVoiceService, OmniVoiceError


# ============================================================================
# Unit Tests (Mocked)
# ============================================================================


class TestOmniVoiceServiceValidation:
    """Test input validation."""

    def test_validate_voice_valid(self):
        """Valid voice should not raise."""
        service = OmniVoiceService()
        for voice in service.VOICE_MAPPING.keys():
            service.validate_voice(voice)  # Should not raise

    def test_validate_voice_invalid(self):
        """Invalid voice should raise ValueError."""
        service = OmniVoiceService()
        with pytest.raises(ValueError, match="Invalid voice"):
            service.validate_voice("invalid_voice")

    def test_validate_text_empty(self):
        """Empty text should raise ValueError."""
        service = OmniVoiceService()
        with pytest.raises(ValueError, match="Text cannot be empty"):
            service.validate_text("")
        with pytest.raises(ValueError, match="Text cannot be empty"):
            service.validate_text("   ")

    def test_validate_text_non_string(self):
        """Non-string text should raise ValueError."""
        service = OmniVoiceService()
        with pytest.raises(ValueError, match="Text must be string"):
            service.validate_text(123)
        with pytest.raises(ValueError, match="Text must be string"):
            service.validate_text(None)

    def test_validate_text_valid(self):
        """Valid text should not raise."""
        service = OmniVoiceService()
        service.validate_text("Xin chào")  # Should not raise


class TestOmniVoiceServiceVoiceMapping:
    """Test voice mapping."""

    def test_all_voices_present(self):
        """All required voices and style presets must be in mapping."""
        expected = {
            "female_young_adult",
            "male_young_adult",
            "female_elderly",
            "male_deep_voice",
            "female_child",
        }
        assert set(OmniVoiceService.VOICE_MAPPING.keys()) == expected

    def test_voice_mapping_non_empty(self):
        """All voice mappings must have non-empty instruct."""
        for voice, instruct in OmniVoiceService.VOICE_MAPPING.items():
            assert isinstance(instruct, str)
            assert len(instruct) > 0


class TestSynthesizeVietnamese:
    """Test synthesize_vietnamese public API."""

    @pytest.mark.parametrize("voice,instruct", [
        ("female_young_adult", "female, young adult"),
        ("male_deep_voice", "male, very low pitch"),
    ])
    @patch("app.services.tts.omnivoice_service.OmniVoiceService.get_model")
    def test_style_instruct_is_passed_to_model(self, mock_get_model, voice, instruct, tmp_path):
        mock_model = MagicMock()
        mock_model.generate.return_value = [np.zeros(240)]
        mock_get_model.return_value = mock_model
        service = OmniVoiceService()

        with patch.object(service, "_generate_output_path", return_value=str(tmp_path / "sample.wav")):
            service.synthesize_vietnamese("Xin chao", "job", voice)

        mock_model.generate.assert_called_once_with(
            text="Xin chao", language="Vietnamese", instruct=instruct, num_step=16
        )

    @patch("app.services.tts.omnivoice_service.OmniVoiceService.get_model")
    def test_synthesize_with_job_id(self, mock_get_model):
        """Test that job_id is used in output filename."""
        mock_model = MagicMock()
        mock_wav = np.random.randn(24000 * 4)
        mock_model.generate.return_value = [mock_wav]
        mock_get_model.return_value = mock_model

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(OmniVoiceService, "_generate_output_path") as mock_path:
                mock_path.return_value = os.path.join(tmpdir, "job_123_female_young_adult.wav")
                
                service = OmniVoiceService()
                result = service.synthesize_vietnamese(
                    "Xin chào",
                    job_id="job_123",
                    voice="female_young_adult"
                )

                # Verify job_id was passed to _generate_output_path
                mock_path.assert_called_once_with("job_123", "female_young_adult")
                mock_model.generate.assert_called_once_with(
                    text="Xin chào",
                    language="Vietnamese",
                    instruct="female, young adult",
                    num_step=16,
                )

    @patch("app.services.tts.omnivoice_service.OmniVoiceService.get_model")
    def test_synthesize_invalid_voice(self, mock_get_model):
        """Test synthesis with invalid voice raises ValueError."""
        service = OmniVoiceService()
        with pytest.raises(ValueError, match="Invalid voice"):
            service.synthesize_vietnamese("Xin chào", "job1", voice="invalid")

    @patch("app.services.tts.omnivoice_service.OmniVoiceService.get_model")
    def test_synthesize_empty_text(self, mock_get_model):
        """Test synthesis with empty text raises ValueError."""
        service = OmniVoiceService()
        with pytest.raises(ValueError, match="Text cannot be empty"):
            service.synthesize_vietnamese("", "job1")

    @patch("app.services.tts.omnivoice_service.OmniVoiceService.get_model")
    def test_synthesize_returns_path(self, mock_get_model):
        """Test that synthesize returns valid WAV path."""
        mock_model = MagicMock()
        mock_wav = np.random.randn(24000 * 4)
        mock_model.generate.return_value = [mock_wav]
        mock_get_model.return_value = mock_model

        with tempfile.TemporaryDirectory() as tmpdir:
            service = OmniVoiceService()
            
            def mock_path_gen(job_id, voice):
                return os.path.join(tmpdir, f"{job_id}_{voice}.wav")
            
            with patch.object(service, "_generate_output_path", side_effect=mock_path_gen):
                result = service.synthesize_vietnamese(
                    "Xin chào",
                    job_id="job1",
                    voice="female_young_adult"
                )

                assert result.endswith(".wav")
                assert os.path.exists(result)
                assert os.path.getsize(result) > 0


class TestModelCaching:
    """Test model singleton caching."""

    @patch("app.services.tts.omnivoice_service.OmniVoiceService.get_model")
    def test_model_load_once(self, mock_get):
        """Model should be loaded and cached."""
        mock_model = MagicMock()
        mock_get.return_value = mock_model

        model1 = OmniVoiceService.get_model()
        model2 = OmniVoiceService.get_model()

        # Both should be the same cached instance
        assert model1 is model2


# ============================================================================
# Integration Test (Real OmniVoice Model)
# ============================================================================


@pytest.mark.integration
class TestOmniVoiceIntegration:
    """Integration tests using real OmniVoice model.
    
    Run with: pytest tests/services/tts/test_omnivoice.py::TestOmniVoiceIntegration -v
    
    Requires: OmniVoice model (~3.2GB) installed
    Time: Several minutes
    """

    @pytest.fixture
    def service(self):
        """Provide OmniVoiceService instance."""
        return OmniVoiceService()

    def test_real_synthesis_all_5_voices(self, service):
        """Test real synthesis with all 5 voices."""
        test_text = "Buổi tối hôm đó, khi mọi người đã ngủ, cô gái vẫn ngồi bên cửa sổ."

        with tempfile.TemporaryDirectory() as tmpdir:
            def mock_path_gen(job_id, voice):
                return os.path.join(tmpdir, f"{job_id}_{voice}.wav")

            with patch.object(service, "_generate_output_path", side_effect=mock_path_gen):
                results = {}
                for voice in service.VOICE_MAPPING.keys():
                    try:
                        path = service.synthesize_vietnamese(
                            test_text,
                            job_id="integration_test",
                            voice=voice
                        )
                        results[voice] = path
                    except Exception as e:
                        pytest.fail(f"Failed for {voice}: {e}")

                # Verify all 5 voices generated files
                assert len(results) == 5
                for voice, path in results.items():
                    assert os.path.exists(path), f"File not created for {voice}"
                    assert os.path.getsize(path) > 0, f"File empty for {voice}"
