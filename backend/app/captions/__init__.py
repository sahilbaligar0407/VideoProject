"""
Speech-to-Text module for ClipGenius Pipeline v2.
Only transcription functionality is kept - caption rendering is handled by external repository.
"""

from .stt import transcribe_audio, detect_language

__all__ = [
    "transcribe_audio",
    "detect_language"
]
