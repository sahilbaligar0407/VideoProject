import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # OpenAI API configuration
    openai_api_key: str = ""
    
    # Video processing configuration
    upload_dir: str = "uploads"
    output_dir: str = "outputs"
    temp_dir: str = "temp"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    supported_formats: List[str] = [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"]
    
    # Clip generation settings
    num_clips: int = 5  # Changed from 3 to 5
    min_clip_duration: float = 20.0
    max_clip_duration: float = 40.0
    target_clip_duration: float = 30.0
    
    # Clip ranking system settings
    ranking_enabled: bool = True
    ranking_weights: dict = {
        "viral_similarity": 0.25,
        "content_engagement": 0.20,
        "audio_analysis": 0.15,
        "story_structure": 0.15,
        "ai_analysis": 0.25
    }
    
    # Whisper transcription settings
    whisper_model: str = "whisper-1"
    
    # Viral similarity engine settings
    viral_terms_file: str = "app/viral/viral_terms.json"
    embed_cache_dir: str = "cache/embeddings"
    viral_vector_file: str = "cache/viral_vector.pkl"
    embedding_model: str = "text-embedding-3-small"
    viral_window_sec: float = 16.0  # Window size in seconds for viral scoring
    viral_window_hop: float = 8.0   # Hop size in seconds for viral scoring
    viral_min_score: float = 0.30   # Minimum score threshold for viral segments
    viral_top_k: int = 12           # Top K segments to return
    viral_max_terms: int = 256      # Maximum terms for viral vector
    
    # Clip length policy
    ending_snap_policy: str = "transcript"  # "transcript", "audio", "none"
    snap_max_overhang: float = 4.0
    snap_silence_thresh_db: float = -35.0
    snap_min_pause: float = 0.25
    snap_punctuations: str = ".!?;:"
    
    # Vertical video settings
    vertical_height: int = 1920
    vertical_width: int = 1080
    vertical_safe_top: int = 100
    vertical_safe_bottom: int = 260
    
    # Transcript file generation settings
    caption_lead_sec: float = 0.18  # Lead-in timing adjustment for Whisper
    min_caption_dur: float = 0.12   # Minimum caption duration
    caption_font: str = "Arial"     # Font for ASS files
    caption_fontsize_vertical: int = 44  # Font size for vertical videos
    caption_outline: int = 3        # Outline width for ASS
    caption_shadow: int = 1         # Shadow for ASS
    
    # Face detection and speaker tracking settings
    face_detection_enabled: bool = True
    face_detection_confidence: float = 0.7
    speaker_tracking_margin: int = 50  # Pixels around detected face
    face_tracking_smoothing: float = 0.8  # Smoothing factor for face tracking
    auto_crop_enabled: bool = True  # Enable automatic cropping to keep speaker centered
    
    # Gaming background settings
    gaming_backgrounds: dict = {
        "subway": "assets/backgrounds/subway/",
        "templerun": "assets/backgrounds/templerun/",
        "minecraft": "assets/backgrounds/minecraft/"
    }
    
    # Topic search settings
    topic_search_enabled: bool = True
    topic_embedding_threshold: float = 0.7
    
    class Config:
        env_file = ".env"

# Create settings instance
settings = Settings()
