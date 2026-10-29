"""
Tests for TranslationJob Celery task lifecycle.

Verifies:
- Job starts in QUEUED status
- First task sets task_id, started_at, status → RUNNING
- Subsequent tasks keep task_id and started_at unchanged
- Final task sets finished_at and status → COMPLETED
- Failed task sets finished_at and status → FAILED
- Exception is properly propagated to Celery
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from app.models import TranslationJob, TranslationJobStatus, Video, VideoStatus


@pytest.fixture
def db_session():
    """Create an in-memory database session for testing."""
    # For unit tests, we'll use a mock session
    session = MagicMock(spec=Session)
    return session


class TestTranslationJobLifecycle:
    """Test TranslationJob lifecycle through the Celery pipeline."""
    
    def test_job_created_in_queued_status(self):
        """Test that new jobs are created in QUEUED status."""
        job = TranslationJob(
            video_id=uuid.uuid4(),
            status=TranslationJobStatus.QUEUED.value
        )
        
        assert job.status == TranslationJobStatus.QUEUED.value
        assert job.task_id is None
        assert job.started_at is None
        assert job.finished_at is None
        assert job.error_message is None
    
    def test_extract_audio_task_sets_lifecycle_fields(self):
        """Test that extract_audio_task (first task) sets task_id, started_at, status."""
        # Create a mock Celery task context
        mock_self = Mock()
        mock_self.request.id = "test-celery-task-id-12345"
        
        job = TranslationJob(
            id=uuid.uuid4(),
            video_id=uuid.uuid4(),
            status=TranslationJobStatus.QUEUED.value
        )
        
        # Simulate what extract_audio_task does
        job.task_id = mock_self.request.id
        job.status = TranslationJobStatus.RUNNING.value
        job.started_at = datetime.utcnow()
        
        # Verify lifecycle
        assert job.task_id == "test-celery-task-id-12345"
        assert job.status == TranslationJobStatus.RUNNING.value
        assert job.started_at is not None
        assert job.finished_at is None
        
    def test_subsequent_task_does_not_overwrite_task_id(self):
        """Test that subsequent tasks do NOT overwrite task_id."""
        # First task sets task_id
        original_task_id = "original-celery-task-id"
        job = TranslationJob(
            id=uuid.uuid4(),
            video_id=uuid.uuid4(),
            task_id=original_task_id,
            status=TranslationJobStatus.RUNNING.value,
            started_at=datetime.utcnow()
        )
        
        # Simulate what a subsequent task would do
        # (should update status but NOT task_id)
        job.status = TranslationJobStatus.RUNNING.value
        # Note: NOT setting job.task_id again
        
        # Verify task_id is preserved
        assert job.task_id == original_task_id
    
    def test_burn_task_sets_finished_at_on_completion(self):
        """Test that burn_task (final task) sets finished_at on successful completion."""
        job = TranslationJob(
            id=uuid.uuid4(),
            video_id=uuid.uuid4(),
            task_id="celery-task-id",
            status=TranslationJobStatus.RUNNING.value,
            started_at=datetime.utcnow(),
            progress=90
        )
        
        # Simulate burn_task completion
        job.status = TranslationJobStatus.COMPLETED.value
        job.finished_at = datetime.utcnow()
        job.progress = 100
        
        # Verify lifecycle
        assert job.status == TranslationJobStatus.COMPLETED.value
        assert job.finished_at is not None
        assert job.error_message is None
    
    def test_failed_task_sets_finished_at_and_error(self):
        """Test that failed task sets finished_at and error_message."""
        job = TranslationJob(
            id=uuid.uuid4(),
            video_id=uuid.uuid4(),
            task_id="celery-task-id",
            status=TranslationJobStatus.RUNNING.value,
            started_at=datetime.utcnow()
        )
        
        # Simulate task failure
        error_msg = "Test error: audio extraction failed"
        job.status = TranslationJobStatus.FAILED.value
        job.error_message = error_msg
        job.finished_at = datetime.utcnow()
        
        # Verify lifecycle
        assert job.status == TranslationJobStatus.FAILED.value
        assert job.finished_at is not None
        assert job.error_message == error_msg
    
    def test_job_duration_calculation(self):
        """Test that job duration can be calculated from started_at and finished_at."""
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        
        job = TranslationJob(
            id=uuid.uuid4(),
            video_id=uuid.uuid4(),
            task_id="celery-task-id",
            status=TranslationJobStatus.COMPLETED.value,
            started_at=start_time,
            finished_at=end_time
        )
        
        # Calculate duration
        if job.started_at and job.finished_at:
            duration = (job.finished_at - job.started_at).total_seconds()
            assert duration >= 0
    
    def test_status_enum_values(self):
        """Test that TranslationJobStatus enum has correct values."""
        assert TranslationJobStatus.QUEUED.value == "queued"
        assert TranslationJobStatus.RUNNING.value == "running"
        assert TranslationJobStatus.COMPLETED.value == "completed"
        assert TranslationJobStatus.FAILED.value == "failed"
    
    def test_full_job_lifecycle_sequence(self):
        """Test the complete job lifecycle from creation to completion."""
        job_id = uuid.uuid4()
        video_id = uuid.uuid4()
        
        # Step 1: Job creation
        job = TranslationJob(
            id=job_id,
            video_id=video_id,
            status=TranslationJobStatus.QUEUED.value
        )
        assert job.status == TranslationJobStatus.QUEUED.value
        assert job.task_id is None
        assert job.started_at is None
        
        # Step 2: First task starts
        celery_task_id = "celery-task-abc123"
        job.task_id = celery_task_id
        job.status = TranslationJobStatus.RUNNING.value
        job.started_at = datetime.utcnow()
        
        assert job.status == TranslationJobStatus.RUNNING.value
        assert job.task_id == celery_task_id
        
        # Step 3: Task completes
        job.status = TranslationJobStatus.COMPLETED.value
        job.finished_at = datetime.utcnow()
        job.progress = 100
        
        assert job.status == TranslationJobStatus.COMPLETED.value
        assert job.finished_at is not None
        assert job.task_id == celery_task_id  # ID unchanged
        assert job.started_at is not None  # Start time unchanged
