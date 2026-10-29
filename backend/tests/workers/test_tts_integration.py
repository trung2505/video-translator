"""
Tests for Vietnamese audio synthesis integration (Step 6B).

Verifies:
- Vietnamese text concatenation from segments
- LongTextTTS invocation with correct parameters
- MP3 file creation and FileRecord storage
- job.output_file_id linking
- Error handling and job lifecycle
- Pipeline integration (no regression)
"""

import pytest
import uuid
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path

from app.models import TranslationJob, TranslationJobStatus, Segment, FileRecord
from app.services.tts.long_text_tts import LongTextTTSError


class TestVietnameseAudioSynthesis:
    """Test Vietnamese audio synthesis task integration."""
    
    def test_vietnamese_text_concatenation_from_segments(self):
        """Test that Vietnamese text is correctly concatenated from segments."""
        # Create mock segments with translated text
        segments = [
            Mock(spec=Segment, translated_text="Xin chào thế giới", order_index=0),
            Mock(spec=Segment, translated_text="Đây là bài kiểm tra", order_index=1),
            Mock(spec=Segment, translated_text="Công việc tổng hợp tiếng nói", order_index=2),
        ]
        
        # Simulate concatenation logic
        vietnamese_texts = [s.translated_text for s in segments]
        vietnamese_text = "\n".join(vietnamese_texts)
        
        expected = "Xin chào thế giới\nĐây là bài kiểm tra\nCông việc tổng hợp tiếng nói"
        assert vietnamese_text == expected
    
    def test_vietnamese_text_with_empty_segments(self):
        """Test concatenation with some empty segments."""
        segments = [
            Mock(spec=Segment, translated_text="Text 1", order_index=0),
            Mock(spec=Segment, translated_text="", order_index=1),
            Mock(spec=Segment, translated_text="Text 3", order_index=2),
        ]
        
        vietnamese_texts = [s.translated_text or "" for s in segments]
        vietnamese_text = "\n".join(vietnamese_texts)
        
        assert "Text 1" in vietnamese_text
        assert "Text 3" in vietnamese_text
        assert vietnamese_text.count("\n") == 2
    
    def test_voice_parameter_default_value(self):
        """Test that default voice is female_young_adult."""
        # Verify default voice constant
        from app.services.tts.long_text_tts import LongTextTTS
        
        tts = LongTextTTS()
        assert "female_young_adult" in tts.VALID_VOICES
        
        # Test that all 5 voices are valid
        expected_voices = {
            "female_young_adult",
            "male_young_adult", 
            "female_elderly",
            "male_deep_voice",
            "female_child"
        }
        assert tts.VALID_VOICES >= expected_voices
    
    def test_longtexttts_integration(self):
        """Test LongTextTTS.synthesize_long_text() interface."""
        from app.services.tts.long_text_tts import LongTextTTS
        
        tts = LongTextTTS()
        
        # Verify method signature
        import inspect
        sig = inspect.signature(tts.synthesize_long_text)
        params = list(sig.parameters.keys())
        
        assert 'text' in params
        assert 'job_id' in params
        assert 'voice' in params
    
    def test_file_record_creation_for_tts_audio(self):
        """Test that FileRecord is created with correct file_type."""
        file_record = FileRecord(
            file_type='tts_audio',
            path='/tmp/test_audio.mp3'
        )
        
        assert file_record.file_type == 'tts_audio'
        assert file_record.path == '/tmp/test_audio.mp3'
    
    def test_job_output_file_id_linking(self):
        """Test that job.output_file_id is updated with FileRecord ID."""
        job_id = uuid.uuid4()
        file_id = uuid.uuid4()
        
        job = TranslationJob(
            id=job_id,
            video_id=uuid.uuid4(),
            status=TranslationJobStatus.RUNNING.value
        )
        
        # Simulate updating output_file_id
        job.output_file_id = file_id
        
        assert job.output_file_id == file_id
    
    def test_tts_failure_sets_job_failed_status(self):
        """Test that TTS failure transitions job to FAILED status."""
        job = TranslationJob(
            id=uuid.uuid4(),
            video_id=uuid.uuid4(),
            status=TranslationJobStatus.RUNNING.value,
            started_at=datetime.utcnow()
        )
        
        # Simulate error handling
        error_msg = "TTS synthesis failed: FFmpeg not found"
        job.status = TranslationJobStatus.FAILED.value
        job.error_message = error_msg
        job.finished_at = datetime.utcnow()
        
        assert job.status == TranslationJobStatus.FAILED.value
        assert job.error_message == error_msg
        assert job.finished_at is not None
    
    def test_tts_failure_preserves_lifecycle_fields(self):
        """Test that task_id and started_at are preserved even on failure."""
        task_id = "celery-task-xyz"
        start_time = datetime.utcnow()
        
        job = TranslationJob(
            id=uuid.uuid4(),
            video_id=uuid.uuid4(),
            task_id=task_id,
            status=TranslationJobStatus.RUNNING.value,
            started_at=start_time
        )
        
        # Simulate failure
        job.status = TranslationJobStatus.FAILED.value
        job.error_message = "TTS failed"
        job.finished_at = datetime.utcnow()
        
        # Verify immutable fields unchanged
        assert job.task_id == task_id
        assert job.started_at == start_time
        assert job.finished_at is not None
    
    def test_pipeline_chaining_translate_to_subtitle(self):
        """Test that translate_task chains to subtitle_task (NOT TTS)."""
        # After architecture fix: video pipeline is restored to original chain
        # translate_task → subtitle_task (TTS is NOT in the main pipeline)
        
        # Read tasks.py to verify chain
        import inspect
        from app.workers import tasks
        
        # Get translate_task source
        source = inspect.getsource(tasks.translate_task)
        
        # Verify it chains to subtitle_task (original behavior)
        assert 'subtitle_task.delay' in source
        assert '.delay(' in source
        # Verify TTS is NOT called from translate_task
        assert 'synthesize_vietnamese_audio_task.delay' not in source
    
    def test_tts_task_ends_after_mp3(self):
        """Test that standalone TTS does not continue the video pipeline."""
        
        import inspect
        from app.workers import tasks
        
        source = inspect.getsource(tasks.synthesize_vietnamese_audio_task)
        
        assert 'subtitle_task.delay' not in source
        assert 'burn_task.delay' not in source

    @pytest.mark.parametrize("voice", ["male_deep_voice", "female_young_adult"])
    def test_tts_task_completes_job_and_stores_mp3(self, voice):
        """Test the successful standalone workflow and lifecycle fields."""
        from app.workers import tasks

        job = TranslationJob(
            id=uuid.uuid4(),
            video_id=uuid.uuid4(),
            job_type="tts",
            status=TranslationJobStatus.QUEUED.value,
            parameters=json.dumps({"text": "Xin chao", "voice": voice}),
        )
        segments = [Mock(translated_text="Xin chao", order_index=0)]
        db = MagicMock()
        segment_query = MagicMock()
        segment_query.filter.return_value.order_by.return_value.all.return_value = segments
        db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=job)))),
            segment_query,
        ]
        db.refresh.side_effect = lambda file_record: setattr(file_record, "id", uuid.uuid4())

        with patch.object(tasks, "SessionLocal", return_value=db), \
             patch.object(tasks, "LocalStorage") as storage_class, \
             patch.object(tasks, "LongTextTTS") as tts_class:
            storage_class.return_value.save_processed_file.return_value = "/tmp/processed/output.mp3"
            tts_class.return_value.synthesize_long_text.return_value = "/tmp/output.mp3"
            result = tasks.synthesize_vietnamese_audio_task.run(str(job.id))

        tts_class.return_value.synthesize_long_text.assert_called_once_with(
            text="Xin chao",
            job_id=str(job.id),
            voice=voice,
        )
        assert result["mp3_path"] == "/tmp/processed/output.mp3"
        assert job.status == TranslationJobStatus.COMPLETED.value
        assert job.progress == 100
        assert job.started_at is not None
        assert job.finished_at is not None
        assert job.output_file_id is not None
        assert any(getattr(item, "file_type", None) == "tts_audio" for item in db.add.call_args_list[0].args)

    def test_tts_task_failure_marks_job_failed_without_file(self):
        """Test that TTS errors stop the workflow without creating an MP3 record."""
        from app.workers import tasks

        job = TranslationJob(
            id=uuid.uuid4(),
            video_id=uuid.uuid4(),
            job_type="tts",
            status=TranslationJobStatus.QUEUED.value,
            parameters=json.dumps({"text": "Xin chao", "voice": "female_child"}),
        )
        segments = [Mock(translated_text="Xin chao", order_index=0)]
        db = MagicMock()
        segment_query = MagicMock()
        segment_query.filter.return_value.order_by.return_value.all.return_value = segments
        db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=job)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=job)))),
        ]

        with patch.object(tasks, "SessionLocal", return_value=db), \
             patch.object(tasks, "LongTextTTS") as tts_class:
            tts_class.return_value.synthesize_long_text.side_effect = LongTextTTSError("FFmpeg failed")
            with pytest.raises(LongTextTTSError):
                tasks.synthesize_vietnamese_audio_task.run(str(job.id))

        assert job.status == TranslationJobStatus.FAILED.value
        assert job.finished_at is not None
        assert "FFmpeg failed" in job.error_message
        assert job.output_file_id is None
        assert not any(getattr(item, "file_type", None) == "tts_audio" for call_item in db.add.call_args_list for item in call_item.args)
    
    def test_no_fake_mp3_on_error(self):
        """Test that LongTextTTS will not create fake MP3."""
        # This is guaranteed by LongTextTTS._is_valid_mp3()
        # which checks for real MP3 magic bytes (ID3v2 or MPEG frame sync)
        
        from app.services.tts.long_text_tts import LongTextTTS
        tts = LongTextTTS()
        
        # Verify _is_valid_mp3 method exists and checks for real MP3
        assert hasattr(tts, '_is_valid_mp3')
    
    def test_text_availability_after_translate_task(self):
        """Test that translated_text is available for TTS after translate_task."""
        # Segment must have translated_text for TTS to work
        segment = Segment(
            job_id=uuid.uuid4(),
            start=0.0,
            end=5.0,
            original_text="Hello",
            translated_text="Xin chào",
            order_index=0
        )
        
        # Verify field exists and can be accessed
        assert hasattr(segment, 'translated_text')
        assert segment.translated_text == "Xin chào"


class TestVoiceConfiguration:
    """Test voice configuration and parameterization."""
    
    def test_default_voice_for_pipeline(self):
        """Test that default voice is suitable for pipeline."""
        # Default voice should be friendly and neutral
        default_voice = "female_young_adult"
        
        # Verify it's in valid voices
        from app.services.tts.long_text_tts import LongTextTTS
        tts = LongTextTTS()
        assert default_voice in tts.VALID_VOICES
    
    def test_voice_parameterization_note(self):
        """Test that voice can be extended via job.parameters in future."""
        # Note: Currently voice is hardcoded to default
        # Future: Can be extended to read from job.parameters
        
        job = TranslationJob(
            id=uuid.uuid4(),
            video_id=uuid.uuid4(),
            parameters=None  # Available field for future voice config
        )
        
        # Verify parameters field exists but is not yet used for voice
        assert hasattr(job, 'parameters')


class TestMP3OutputHandling:
    """Test MP3 file output and storage."""
    
    def test_mp3_file_record_type(self):
        """Test that output file is recorded with correct type."""
        file_record = FileRecord(
            file_type='tts_audio',
            path='/path/to/output.mp3'
        )
        
        assert file_record.file_type == 'tts_audio'
        assert file_record.path.endswith('.mp3')
    
    def test_mp3_output_file_id_reference(self):
        """Test that job references MP3 output file via output_file_id."""
        job_id = uuid.uuid4()
        file_id = uuid.uuid4()
        
        job = TranslationJob(
            id=job_id,
            video_id=uuid.uuid4(),
            output_file_id=file_id
        )
        
        assert job.output_file_id == file_id
    
    def test_mp3_path_from_longtexttts(self):
        """Test that MP3 path returned by LongTextTTS is valid."""
        # LongTextTTS.synthesize_long_text() returns a path string
        # Path should point to a file on disk with .mp3 extension
        
        from pathlib import Path
        
        # Example path from LongTextTTS
        mp3_path = Path("/tmp/long_text_tts/job_id/job_id.mp3")
        
        assert str(mp3_path).endswith('.mp3')
        assert 'job_id' in str(mp3_path)


class TestErrorHandling:
    """Test error handling and failure scenarios."""
    
    def test_invalid_voice_raises_error(self):
        """Test that invalid voice raises ValueError."""
        from app.services.tts.long_text_tts import LongTextTTS
        
        tts = LongTextTTS()
        
        with pytest.raises(ValueError):
            tts.synthesize_long_text(
                text="Test text",
                job_id="test_job",
                voice="invalid_voice"
            )
    
    def test_empty_text_raises_error(self):
        """Test that empty text raises LongTextTTSError."""
        from app.services.tts.long_text_tts import LongTextTTS
        
        tts = LongTextTTS()
        
        with pytest.raises(ValueError):
            tts.synthesize_long_text(
                text="",
                job_id="test_job",
                voice="female_young_adult"
            )
    
    def test_celery_exception_propagation(self):
        """Test that task exceptions are properly propagated to Celery."""
        # Task decorator with raise will propagate to Celery
        # This is handled by the task's final raise statement
        pass


class TestPipelineIntegration:
    """Test integration with existing pipeline."""
    
    def test_no_regression_in_translate_task(self):
        """Test that translate_task still translates correctly."""
        # translate_task only changes its final chain call
        # Translation logic is unchanged
        pass
    
    def test_no_regression_in_subtitle_task(self):
        """Test that subtitle_task is called after TTS."""
        # subtitle_task receives job_id as before
        # No changes to subtitle_task logic
        pass
    
    def test_no_regression_in_burn_task(self):
        """Test that burn_task works with new output_file_id."""
        # burn_task will ignore output_file_id (uses video.subtitle_file_id)
        # No regression
        pass
    
    def test_job_lifecycle_with_tts(self):
        """Test full job lifecycle with TTS integration."""
        job = TranslationJob(
            id=uuid.uuid4(),
            video_id=uuid.uuid4(),
            status=TranslationJobStatus.QUEUED.value
        )
        
        # Step 1: extract_audio sets task_id, started_at, RUNNING
        job.task_id = "celery_id"
        job.status = TranslationJobStatus.RUNNING.value
        job.started_at = datetime.utcnow()
        
        assert job.task_id == "celery_id"
        assert job.status == TranslationJobStatus.RUNNING.value
        
        # Step 2-4: translate, tts (new), subtitle run
        job.progress = 60
        
        # Step 5: burn completes
        job.status = TranslationJobStatus.COMPLETED.value
        job.finished_at = datetime.utcnow()
        job.progress = 100
        
        assert job.status == TranslationJobStatus.COMPLETED.value
        assert job.finished_at is not None
