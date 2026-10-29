from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class VideoResponse(BaseModel):
    id: str
    original_filename: str
    upload_date: datetime
    status: str
    progress: int
    duration: Optional[float]
    file_size: int
    error_message: Optional[str]
    
    class Config:
        from_attributes = True

class TranslationJobResponse(BaseModel):
    id: str
    video_id: str
    status: str
    progress: int
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


TTSVoice = Literal[
    "female_young_adult",
    "male_young_adult",
    "female_elderly",
    "male_deep_voice",
    "female_child",
]


class TTSCreateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100_000)
    voice: TTSVoice = "female_young_adult"

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Text cannot be empty")
        return value


class TTSJobResponse(BaseModel):
    id: str
    job_type: str
    status: str
    progress: int
    voice: str
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    output_file_id: Optional[str] = None
    error_message: Optional[str] = None

class TranslationStartRequest(BaseModel):
    video_id: str

class TranslationStartResponse(BaseModel):
    id: str
    video_id: str
    status: str
    message: str

class VideoStatusResponse(BaseModel):
    video_id: str
    video_status: str
    video_progress: int
    job_id: Optional[str] = None
    job_status: Optional[str] = None

    class Config:
        from_attributes = True
