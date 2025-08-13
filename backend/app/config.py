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
    
    class Config:
        env_file = ".env"

settings = Settings()

# Create necessary directories
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.output_dir, exist_ok=True)
os.makedirs(settings.temp_dir, exist_ok=True)
