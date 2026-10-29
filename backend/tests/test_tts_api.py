import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.api.schemas import TTSCreateRequest, TTSJobResponse
from app.api import tts
from app.models import FileRecord, TranslationJob, TranslationJobStatus


def test_tts_request_validates_text_and_voice():
    request = TTSCreateRequest(text="  Xin chao  ", voice="female_child")
    assert request.text == "Xin chao"
    assert request.voice == "female_child"

    with pytest.raises(ValidationError):
        TTSCreateRequest(text=" ", voice="female_child")
    with pytest.raises(ValidationError):
        TTSCreateRequest(text="Xin chao", voice="unknown_voice")
    with pytest.raises(ValidationError):
        TTSCreateRequest(text="x" * 100_001, voice="female_child")


@pytest.mark.parametrize("voice", ["female_young_adult", "male_young_adult", "female_elderly", "male_deep_voice", "female_child"])
def test_create_tts_job_stores_text_and_enqueues_task(voice):
    db = MagicMock()
    job = TranslationJob(id=uuid.uuid4(), job_type="tts", status=TranslationJobStatus.QUEUED.value)
    db.refresh.side_effect = lambda value: setattr(value, "id", job.id)
    request = TTSCreateRequest(text="Xin chao Viet Nam", voice=voice)

    with patch.object(tts, "TranslationJob", return_value=job) as job_model, \
         patch.object(tts.synthesize_vietnamese_audio_task, "delay") as delay:
        response = tts.create_tts_job(request, db)

    job_model.assert_called_once()
    created_kwargs = job_model.call_args.kwargs
    assert created_kwargs["video_id"] is None
    assert created_kwargs["job_type"] == "tts"
    assert json.loads(created_kwargs["parameters"]) == {
        "text": "Xin chao Viet Nam",
        "voice": voice,
    }
    delay.assert_called_once_with(str(job.id))
    assert response["status"] == TranslationJobStatus.QUEUED.value


@pytest.mark.parametrize("voice", [
    "female_sweet", "female_expressive", "capcut_bv421_vivn_streaming", "BV074_streaming",
])
def test_unavailable_voice_cannot_be_requested(voice):
    with pytest.raises(ValidationError):
        TTSCreateRequest(text="Xin chao", voice=voice)


@pytest.mark.parametrize("voice", ["female_sweet", "female_expressive"])
def test_legacy_voice_remains_readable_in_job_response(voice):
    response = TTSJobResponse(id="job", job_type="tts", status="completed", progress=100, voice=voice)
    assert response.voice == voice


def test_get_tts_job_returns_status_and_voice():
    job = TranslationJob(
        id=uuid.uuid4(),
        job_type="tts",
        status=TranslationJobStatus.RUNNING.value,
        progress=45,
        parameters=json.dumps({"text": "Xin chao", "voice": "female_elderly"}),
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = job

    response = tts.get_tts_job(str(job.id), db)

    assert response["status"] == "running"
    assert response["progress"] == 45
    assert response["voice"] == "female_elderly"


def test_download_tts_audio_requires_completed_job_and_returns_mp3(tmp_path: Path):
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"ID3fake")
    file_record = FileRecord(id=uuid.uuid4(), file_type="tts_audio", path=str(audio_path))
    job = TranslationJob(
        id=uuid.uuid4(),
        job_type="tts",
        status=TranslationJobStatus.COMPLETED.value,
        output_file_id=file_record.id,
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [job, file_record]

    response = tts.download_tts_audio(str(job.id), db)

    assert response.media_type == "audio/mpeg"
    assert response.filename == f"vietnamese_tts_{job.id}.mp3"


def test_download_tts_audio_rejects_incomplete_job():
    job = TranslationJob(
        id=uuid.uuid4(),
        job_type="tts",
        status=TranslationJobStatus.RUNNING.value,
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = job

    with pytest.raises(Exception) as error:
        tts.download_tts_audio(str(job.id), db)

    assert error.value.status_code == 409
