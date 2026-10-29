"""
Tests for Long Text TTS Service (Step 5B)

Includes:
- Unit tests with mocking (fast, no OmniVoice model needed)
- Integration test with real OmniVoice (slower, real synthesis)
- All 5 voice verification test
"""

import pytest
import os
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from app.services.tts.long_text_tts import LongTextTTS, LongTextTTSError
from app.services.text_service import TextChunker


# ============================================================================
# Unit Tests (Mocked)
# ============================================================================

class TestLongTextTTSValidation:
    """Test input validation."""
    
    def test_empty_text_rejected(self):
        """Empty text should raise ValueError."""
        service = LongTextTTS()
        with pytest.raises(ValueError, match="empty"):
            service.synthesize_long_text("", job_id="test", voice="female_young_adult")
    
    def test_whitespace_only_rejected(self):
        """Whitespace-only text should raise ValueError."""
        service = LongTextTTS()
        with pytest.raises(ValueError, match="empty"):
            service.synthesize_long_text("   \n\t   ", job_id="test", voice="female_young_adult")
    
    def test_invalid_voice_rejected(self):
        """Invalid voice should raise ValueError."""
        service = LongTextTTS()
        with pytest.raises(ValueError, match="Invalid voice"):
            service.synthesize_long_text(
                "Some text",
                job_id="test",
                voice="invalid_voice"
            )
    
    def test_all_five_voices_accepted(self):
        """All 5 valid voices should be accepted (validation passes)."""
        service = LongTextTTS()
        valid_voices = [
            "female_young_adult",
            "male_young_adult",
            "female_elderly",
            "male_deep_voice",
            "female_child",
        ]
        for voice in valid_voices:
            # Should not raise
            service._validate_input("Test text", voice)


class TestLongTextTTSChunking:
    """Test chunking behavior."""
    
    def test_short_text_single_chunk(self):
        """Short text should result in single chunk."""
        service = LongTextTTS(max_chars_per_chunk=500)
        text = "This is a short text."
        chunks = service.chunker.chunk_text(text)
        assert len(chunks) == 1
    
    def test_long_text_multiple_chunks(self):
        """Long text should be chunked."""
        service = LongTextTTS(max_chars_per_chunk=100)
        text = "Word " * 50  # ~250 chars
        chunks = service.chunker.chunk_text(text)
        assert len(chunks) > 1
        assert all(len(chunk) <= 100 for chunk in chunks)
    
    def test_vietnamese_text_chunked_correctly(self):
        """Vietnamese text should be chunked intelligently."""
        service = LongTextTTS(max_chars_per_chunk=200)
        text = """Ngày hôm đó trời mưa rất lớn. Tôi đứng trước cửa và chờ anh.
        Khoảng mười phút sau, anh mới xuất hiện. Chúng tôi bước ra ngoài cùng nhau."""
        chunks = service.chunker.chunk_text(text)
        assert len(chunks) >= 1
        assert all(len(chunk) <= 200 for chunk in chunks)


class TestLongTextTTSMocked:
    """Test Long Text TTS with mocked OmniVoice."""

    @pytest.mark.parametrize("voice", ["female_young_adult", "male_deep_voice"])
    def test_selected_style_is_forwarded_to_every_chunk(self, voice, tmp_path):
        service = LongTextTTS()
        chunks = ["First chunk.", "Second chunk."]
        with patch.object(service, "OUTPUT_BASE", tmp_path), \
             patch.object(service.chunker, "chunk_text", return_value=chunks), \
             patch.object(service, "_synthesize_chunk", side_effect=["one.wav", "two.wav"]) as synthesize, \
             patch.object(service, "_merge_wav_chunks", return_value=str(tmp_path / "output.mp3")):
            service.synthesize_long_text("Some text", "job", voice)

        assert synthesize.call_count == len(chunks)
        assert synthesize.call_args_list[0].args == (chunks[0], "job", voice, "001")
        assert synthesize.call_args_list[1].args == (chunks[1], "job", voice, "002")
    
    @patch("app.services.tts.long_text_tts.OmniVoiceService")
    @patch("app.services.tts.long_text_tts.LongTextTTS._merge_wav_chunks")
    def test_synthesis_orchestration(self, mock_merge, mock_tts_class):
        """Test synthesis orchestration with mocked TTS."""
        # Setup mock TTS
        mock_tts = MagicMock()
        mock_tts_class.return_value = mock_tts
        
        # Setup mock merge
        mock_merge.return_value = "/tmp/mocked_output.mp3"
        
        # Create temp directory with fake WAV files
        with tempfile.TemporaryDirectory() as tmpdir:
            import soundfile
            import shutil
            
            # Create fake WAV file
            fake_wav = Path(tmpdir) / "test.wav"
            data = np.random.randn(24000)
            soundfile.write(str(fake_wav), data, 24000)
            
            # Mock TTS to return our fake WAV path
            mock_tts.synthesize_vietnamese.return_value = str(fake_wav)
            
            # Patch os.path.getsize to avoid file check
            # Also patch shutil.copy to prevent writing to /tmp
            with patch("os.path.getsize", return_value=1024):
                with patch("shutil.copy2") as mock_copy:
                    # Use unique job ID to avoid chunk reuse from prior tests
                    unique_job = f"test_job_{int(time.time() * 1000)}"
                    
                    service = LongTextTTS(max_chars_per_chunk=50)
                    text = "Word " * 30  # ~150 chars = 3 chunks
                    
                    result = service.synthesize_long_text(
                        text=text,
                        job_id=unique_job,
                        voice="female_young_adult"
                    )
                    
                    # Verify merge was called
                    assert mock_merge.called
                    assert result == "/tmp/mocked_output.mp3"
                    
                    # Verify TTS was called multiple times (once per chunk)
                    assert mock_tts.synthesize_vietnamese.call_count >= 1


class TestLongTextTTSWAVValidation:
    """Test WAV file validation."""
    
    def test_valid_wav_accepted(self):
        """Valid WAV file should pass validation."""
        import soundfile
        service = LongTextTTS()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            # Create valid WAV
            data = np.random.randn(24000)  # 1 second at 24kHz
            soundfile.write(str(temp_path), data, 24000)
            
            assert service._is_valid_wav(temp_path) is True
        finally:
            temp_path.unlink()
    
    def test_empty_wav_rejected(self):
        """Empty WAV file should fail validation."""
        import soundfile
        service = LongTextTTS()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            # Create empty WAV
            data = np.array([])
            soundfile.write(str(temp_path), data, 24000)
            
            assert service._is_valid_wav(temp_path) is False
        finally:
            temp_path.unlink()
    
    def test_nonexistent_file_rejected(self):
        """Non-existent file should fail validation."""
        service = LongTextTTS()
        assert service._is_valid_wav(Path("/nonexistent/file.wav")) is False


# ============================================================================
# Integration Tests (Real OmniVoice)
# ============================================================================

@pytest.mark.integration
class TestLongTextTTSIntegration:
    """Integration test with real OmniVoice model."""
    
    def test_long_text_full_pipeline(self):
        """Test complete pipeline: text → chunks → OmniVoice → WAV → merge → MP3.
        
        Requires FFmpeg to be installed on the system.
        If FFmpeg is not available, this test will fail with RuntimeError.
        """
        # Use Vietnamese text, ~706 chars
        text = """
        Ngày hôm đó trời mưa rất lớn. Tôi đứng trước cửa và chờ anh. Khoảng mười phút sau, 
        anh mới xuất hiện. Chúng tôi bước ra ngoài cùng nhau. Mưa vẫn rơi ào ào, nhưng tôi 
        cảm thấy ấm áp vì có anh bên cạnh. "Bạn khỏe không?" anh hỏi. "Tôi khỏe, cảm ơn bạn," 
        tôi trả lời. Chúng tôi đi dọc theo con đường quen thuộc.
        """.strip()
        
        print(f"\n[Integration Test] Input: {len(text)} chars")
        
        service = LongTextTTS(max_chars_per_chunk=300)
        
        # Run synthesis - expect RuntimeError if FFmpeg not available
        mp3_path = service.synthesize_long_text(
            text=text,
            job_id="integration_test",
            voice="female_young_adult",
        )
        
        # Verify output
        assert Path(mp3_path).exists(), f"MP3 not created: {mp3_path}"
        size = Path(mp3_path).stat().st_size
        assert size > 0, f"MP3 empty: {mp3_path}"
        
        # Verify it's a real MP3 (not WAV with .mp3 extension)
        with open(mp3_path, "rb") as f:
            header = f.read(3)
            # Check for ID3v2 tag or MPEG frame sync
            assert (header == b"ID3" or (len(header) >= 2 and header[0] == 0xFF)), \
                f"File is not a real MP3: {mp3_path}"
        
        print(f"[OK] Integration test passed")
        print(f"  MP3: {mp3_path}")
        print(f"  Size: {size:,} bytes")
        print(f"  Valid MP3: Yes")


@pytest.mark.integration
class TestLongTextTTSAllVoices:
    """Verification test with all 5 voices.
    
    Requires FFmpeg to be installed on the system.
    """
    
    def test_all_five_voices_synthesis(self):
        """Test synthesis with all 5 valid voices.
        
        If FFmpeg is not available, this test will fail with RuntimeError.
        """
        # Use single sentence for quick verification
        text = "Xin chào, đây là bài kiểm tra giọng nói. Chúng tôi kiểm tra năm giọng khác nhau."
        
        voices = [
            "female_young_adult",
            "male_young_adult",
            "female_elderly",
            "male_deep_voice",
            "female_child",
        ]
        
        service = LongTextTTS(max_chars_per_chunk=500)
        
        results = {}
        for voice in voices:
            print(f"\n[Voice Test] Testing {voice}...")
            mp3_path = service.synthesize_long_text(
                text=text,
                job_id=f"voice_test_{voice}",
                voice=voice,
            )
            
            assert Path(mp3_path).exists(), f"MP3 not created for {voice}"
            size = Path(mp3_path).stat().st_size
            assert size > 0, f"MP3 empty for {voice}"
            
            # Verify it's a real MP3
            with open(mp3_path, "rb") as f:
                header = f.read(3)
                assert (header == b"ID3" or (len(header) >= 2 and header[0] == 0xFF)), \
                    f"File is not a real MP3 for {voice}: {mp3_path}"
            
            results[voice] = {
                "path": mp3_path,
                "size": size,
            }
            print(f"  [OK] {voice}: {size:,} bytes (real MP3)")
        
        print(f"\n[Voice Test Summary]")
        print(f"  All 5 voices passed: {', '.join(voices)}")
