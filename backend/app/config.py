import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # OpenAI API Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # File Storage Configuration
    upload_dir: str = "uploads"
    output_dir: str = "outputs"
    temp_dir: str = "temp"
    
    # Video Processing Configuration
    max_file_size: int = 500 * 1024 * 1024  # 500MB
    supported_formats: list = [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv"]
    
    # Highlight Generation Configuration
    min_clip_duration: int = 15  # seconds (optimized for short-form)
    max_clip_duration: int = 60  # seconds (max for TikTok/Reels)
    num_clips: int = 3
    
    # Whisper API Configuration
    whisper_model: str = "whisper-1"
    
    # Viral Similarity Engine Configuration
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    viral_window_sec: float = float(os.getenv("VIRAL_WINDOW_SEC", "16"))
    viral_window_hop: float = float(os.getenv("VIRAL_WINDOW_HOP", "8"))
    viral_min_score: float = float(os.getenv("VIRAL_MIN_SCORE", "0.30"))
    viral_top_k: int = int(os.getenv("VIRAL_TOP_K", "12"))
    viral_max_terms: int = int(os.getenv("VIRAL_MAX_TERMS", "256"))
    embed_cache_dir: str = os.getenv("EMBED_CACHE_DIR", "./.embed_cache")
    
    class Config:
        env_file = ".env"

settings = Settings()

# Create necessary directories
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.output_dir, exist_ok=True)
os.makedirs(settings.temp_dir, exist_ok=True)
os.makedirs(settings.embed_cache_dir, exist_ok=True)
