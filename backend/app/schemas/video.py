from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class VideoCreateResponse(BaseModel):
    id: UUID
    message: Optional[str] = None


class VideoStatusResponse(BaseModel):
    video_id: UUID
    video_status: str
    video_progress: int
    job_id: Optional[str] = None
    job_status: Optional[str] = None
