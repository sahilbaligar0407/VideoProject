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
    num_clips: int = 3
    min_clip_duration: float = 20.0
    max_clip_duration: float = 40.0
    target_clip_duration: float = 30.0
    
    # Whisper transcription settings
    whisper_model: str = "whisper-1"
    
    # Viral similarity engine settings
    viral_terms_file: str = "app/viral/viral_terms.json"
    embed_cache_dir: str = "cache/embeddings"
    viral_vector_file: str = "cache/viral_vector.pkl"
    embedding_model: str = "text-embedding-3-small"
    
    # Clip length policy
    ending_snap_policy: str = "transcript"  # "transcript", "audio", "none"
    snap_max_overhang: float = 4.0
    snap_silence_thresh_db: float = -35.0
    snap_min_pause: float = 0.25
    snap_punctuations: str = ".!?;:"
    
    # Vertical video settings
    vertical_height: int = 1920
    vertical_safe_top: int = 100
    vertical_safe_bottom: int = 100
    
    # Caption settings
    caption_mode: str = "sidecar"  # "burn", "sidecar", "off"
    caption_theme: dict = {
        "font": "Inter",
        "fontsize_vertical": 44,
        "fontsize_horizontal": 36,
        "outline": 3,
        "shadow": 1,
        "primary_hex": "#FFFFFF",
        "outline_hex": "#000000",
        "vertical_margin_top": 160,
        "vertical_margin_bottom": 260,
        "horizontal_margin_bottom": 120,
        "max_width_pct": 0.9
    }
    
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
