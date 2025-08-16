"""
Feature configuration for ClipGenius Pipeline v2.
Defines user toggles and advanced settings.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class CaptionMode(str, Enum):
    """Caption rendering modes"""
    BURN = "burn"
    SIDECAR = "sidecar"
    OFF = "off"

class CaptionStyle(str, Enum):
    """Caption styling options"""
    BOXED = "boxed"
    OUTLINE = "outline"
    KARAOKE = "karaoke"
    DEFAULT = "default"

class BackgroundMode(str, Enum):
    """Background rendering modes"""
    BLUR = "blur"
    GAMEPLAY = "gameplay"
    NONE = "none"

class GameTheme(str, Enum):
    """Gaming background themes"""
    SUBWAY = "subway"
    TEMPLERUN = "templerun"
    MINECRAFT = "minecraft"

class CTAType(str, Enum):
    """Call-to-action types"""
    AUTO = "auto"
    SUBSCRIBE = "subscribe"
    FOLLOW = "follow"
    COMMENT = "comment"
    LIKE = "like"
    SHARE = "share"

class CaptionConfig(BaseModel):
    """Caption configuration"""
    mode: CaptionMode = CaptionMode.SIDECAR
    language: str = "auto"
    style: CaptionStyle = CaptionStyle.DEFAULT
    safe_bottom: int = 160  # pixels from bottom
    max_lines: int = 2
    word_by_word: bool = False

class BackgroundConfig(BaseModel):
    """Background configuration"""
    mode: BackgroundMode = BackgroundMode.BLUR
    game: Optional[GameTheme] = None
    mute: bool = True
    blur_strength: int = 40

class FaceTrackingConfig(BaseModel):
    """Face tracking configuration"""
    enabled: bool = True
    min_confidence: float = 0.5
    smoothing_window: int = 5
    transition_duration: float = 0.4

class AIConfig(BaseModel):
    """AI features configuration"""
    auto_titles: bool = True
    cta: CTAType = CTAType.AUTO
    model: str = "gpt-4o"
    temperature: float = 0.7

class VideoConfig(BaseModel):
    """Video output configuration"""
    duration_target: float = 28.0
    fps: int = 30
    resolution: str = "1080x1920"
    quality: str = "high"  # high, medium, low

class PipelineConfig(BaseModel):
    """Main pipeline configuration"""
    captions: CaptionConfig = CaptionConfig()
    background: BackgroundConfig = BackgroundConfig()
    face_tracking: FaceTrackingConfig = FaceTrackingConfig()
    ai: AIConfig = AIConfig()
    video: VideoConfig = VideoConfig()
    
    # Advanced settings
    enable_scene_detection: bool = True
    enable_speech_analysis: bool = True
    enable_viral_scoring: bool = True
    enable_hook_detection: bool = True

def get_default_config() -> PipelineConfig:
    """Get default pipeline configuration"""
    return PipelineConfig()

def load_config_from_dict(config_dict: Dict[str, Any]) -> PipelineConfig:
    """Load configuration from dictionary"""
    try:
        return PipelineConfig(**config_dict)
    except Exception as e:
        print(f"⚠️ Config loading failed, using defaults: {e}")
        return get_default_config()

def validate_config(config: PipelineConfig) -> List[str]:
    """Validate configuration and return list of warnings"""
    warnings = []
    
    # Validate caption settings
    if config.captions.mode == CaptionMode.BURN and config.captions.word_by_word:
        warnings.append("Word-by-word captions not supported in burn mode")
    
    # Validate background settings
    if config.background.mode == BackgroundMode.GAMEPLAY and not config.background.game:
        warnings.append("Game theme required when using gameplay background")
    
    # Validate face tracking
    if config.face_tracking.min_confidence < 0.1 or config.face_tracking.min_confidence > 0.9:
        warnings.append("Face tracking confidence should be between 0.1 and 0.9")
    
    # Validate video settings
    if config.video.duration_target < 10 or config.video.duration_target > 60:
        warnings.append("Duration target should be between 10 and 60 seconds")
    
    if config.video.fps not in [24, 25, 30, 50, 60]:
        warnings.append("FPS should be one of: 24, 25, 30, 50, 60")
    
    return warnings

def get_config_summary(config: PipelineConfig) -> Dict[str, Any]:
    """Get human-readable configuration summary"""
    return {
        "captions": {
            "mode": config.captions.mode.value,
            "language": config.captions.language,
            "style": config.captions.style.value
        },
        "background": {
            "mode": config.background.mode.value,
            "game": config.background.game.value if config.background.game else None,
            "mute": config.background.mute
        },
        "face_tracking": {
            "enabled": config.face_tracking.enabled,
            "confidence_threshold": config.face_tracking.min_confidence
        },
        "ai_features": {
            "auto_titles": config.ai.auto_titles,
            "cta": config.ai.cta.value,
            "model": config.ai.model
        },
        "video": {
            "target_duration": f"{config.video.duration_target}s",
            "fps": config.video.fps,
            "resolution": config.video.resolution,
            "quality": config.video.quality
        }
    }

# Preset configurations
def get_podcast_preset() -> PipelineConfig:
    """Get optimized preset for podcast content"""
    config = get_default_config()
    config.captions.mode = CaptionMode.SIDECAR
    config.captions.language = "auto"
    config.face_tracking.enabled = True
    config.background.mode = BackgroundMode.BLUR
    config.ai.auto_titles = True
    config.video.duration_target = 30.0
    return config

def get_gaming_preset() -> PipelineConfig:
    """Get optimized preset for gaming content"""
    config = get_default_config()
    config.captions.mode = CaptionMode.BURN
    config.captions.style = CaptionStyle.OUTLINE
    config.face_tracking.enabled = False
    config.background.mode = BackgroundMode.GAMEPLAY
    config.background.game = GameTheme.SUBWAY
    config.ai.auto_titles = True
    config.video.duration_target = 25.0
    return config

def get_educational_preset() -> PipelineConfig:
    """Get optimized preset for educational content"""
    config = get_default_config()
    config.captions.mode = CaptionMode.SIDECAR
    config.captions.language = "auto"
    config.captions.word_by_word = True
    config.face_tracking.enabled = True
    config.background.mode = BackgroundMode.BLUR
    config.ai.auto_titles = True
    config.ai.cta = CTAType.SUBSCRIBE
    config.video.duration_target = 35.0
    return config

def get_preset_config(preset_name: str) -> Optional[PipelineConfig]:
    """Get configuration preset by name"""
    presets = {
        "podcast": get_podcast_preset,
        "gaming": get_gaming_preset,
        "educational": get_educational_preset,
        "default": get_default_config
    }
    
    if preset_name in presets:
        return presets[preset_name]()
    
    return None
