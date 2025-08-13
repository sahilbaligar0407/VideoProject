from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class VideoInput(BaseModel):
    """Input model for video processing requests"""
    youtube_url: Optional[str] = None
    file_path: Optional[str] = None

class TranscriptionResult(BaseModel):
    """Model for transcription results"""
    text: str
    segments: List[dict]
    language: str
    duration: float

class HighlightSegment(BaseModel):
    """Model for detected highlight segments"""
    start_time: float
    end_time: float
    duration: float
    confidence_score: float
    keywords: List[str]
    transcript_segment: str

class GeneratedClip(BaseModel):
    """Model for generated highlight clips"""
    clip_id: str
    start_time: float
    end_time: float
    duration: float
    file_path: str
    thumbnail_path: Optional[str] = None
    caption_text: str
    download_url: str

class ProcessingStatus(BaseModel):
    """Model for processing status updates"""
    status: str  # "processing", "completed", "failed"
    progress: int  # 0-100
    message: str
    current_step: str
    estimated_time: Optional[int] = None

class VideoProcessingRequest(BaseModel):
    """Model for video processing requests"""
    request_id: str
    input_type: str  # "youtube" or "file"
    input_source: str
    status: ProcessingStatus
    created_at: datetime
    updated_at: datetime
    clips: Optional[List[GeneratedClip]] = None
    error_message: Optional[str] = None

class VideoProcessingResponse(BaseModel):
    """Model for video processing responses"""
    request_id: str
    status: str
    message: str
    clips: Optional[List[GeneratedClip]] = None
    error: Optional[str] = None
