from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
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

class ClipRanking(BaseModel):
    """Model for clip ranking and virality scoring"""
    viral_score: float  # 0.0 to 5.0 scale
    engagement_potential: float  # 0.0 to 1.0
    shareability: float  # 0.0 to 1.0
    trending_potential: float  # 0.0 to 1.0
    ranking_factors: Dict[str, float]  # Detailed breakdown of scoring factors

class HighlightSegment(BaseModel):
    """Model for detected highlight segments"""
    model_config = ConfigDict(extra="allow")  # Allow extra fields for backward compatibility
    
    start_time: float
    end_time: float
    duration: float
    confidence_score: float
    keywords: List[str]
    transcript_segment: str
    detection_method: Optional[str] = None  # Method used to detect this highlight
    ranking: Optional[ClipRanking] = None  # Ranking information (added by ClipRanker)

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
    ranking: Optional[ClipRanking] = None  # New ranking information
    face_tracking_applied: bool = False  # Whether face tracking was used
    speaker_centered: bool = False  # Whether speaker was kept centered

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


# Viral Similarity Engine Models
class ViralTerm(BaseModel):
    """Model for viral terms with weights."""
    term: str
    weight: float = 1.0


class ScoredWindow(BaseModel):
    """A caption window with its viral similarity score."""
    start_time: float
    end_time: float
    score: float
    text: str


class ViralScoringRequest(BaseModel):
    """Request model for viral scoring."""
    captions: List[Dict[str, Any]]
    video_duration: float


class ViralScoringResponse(BaseModel):
    """Response model for viral scoring."""
    video_id: str
    scored_windows: List[ScoredWindow]
    total_windows: int
    viral_vector_info: Dict[str, Any]


class ViralTermsResponse(BaseModel):
    """Response model for viral terms management."""
    terms: List[ViralTerm]
    total_count: int
    max_terms: int


class ViralVectorResponse(BaseModel):
    """Response model for viral vector operations."""
    vector_size: int
    updated_at: str
    model: str
    terms_count: int
