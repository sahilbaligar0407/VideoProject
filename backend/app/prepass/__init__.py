"""
Prepass detection modules for ClipGenius Pipeline v2.
"""

from .faces import track_faces, smooth_boxes, FrameBox, has_face_in_range, FaceTracker
from .speech import detect_speech_segments
from .shots import detect_scene_changes

__all__ = [
    "track_faces",
    "smooth_boxes", 
    "FrameBox",
    "has_face_in_range",
    "FaceTracker",
    "detect_speech_segments",
    "detect_scene_changes"
]
