"""
Highlight detection and snapping utilities for ClipGenius.
"""

from .snapping import (
    snap_to_transcript_boundary,
    snap_to_audio_pause,
    choose_clip_window,
    duration_preference
)

__all__ = [
    "snap_to_transcript_boundary",
    "snap_to_audio_pause", 
    "choose_clip_window",
    "duration_preference"
]
