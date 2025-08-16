"""
Scene change detection for ClipGenius Pipeline v2.
Uses simple HSV difference detection to avoid hard cuts during transitions.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class SceneChange:
    """Scene change detection result"""
    timestamp: float
    confidence: float
    change_type: str  # "hard_cut", "fade", "zoom"

def detect_scene_changes(video_path: str, sample_rate: int = 5, 
                        threshold: float = 0.15) -> List[SceneChange]:
    """
    Detect scene changes in a video using HSV histogram differences
    
    Args:
        video_path: Path to video file
        sample_rate: Sample every Nth frame (default: 5 = 6fps for 30fps video)
        threshold: Threshold for detecting significant changes
        
    Returns:
        List of SceneChange objects
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Could not open video: {video_path}")
        return []
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"🎬 Detecting scene changes in {video_path}")
    print(f"   FPS: {fps:.1f}, Total frames: {total_frames}")
    
    scene_changes = []
    prev_hist = None
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Sample every Nth frame
        if frame_count % sample_rate == 0:
            timestamp = frame_count / fps
            
            # Convert to HSV and calculate histogram
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
            hist = cv2.normalize(hist, hist).flatten()
            
            if prev_hist is not None:
                # Calculate histogram difference
                diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                change_score = 1.0 - diff  # Convert correlation to difference
                
                if change_score > threshold:
                    # Determine change type based on magnitude
                    if change_score > 0.8:
                        change_type = "hard_cut"
                    elif change_score > 0.5:
                        change_type = "fade"
                    else:
                        change_type = "zoom"
                    
                    scene_change = SceneChange(
                        timestamp=timestamp,
                        confidence=change_score,
                        change_type=change_type
                    )
                    scene_changes.append(scene_change)
                    
                    if frame_count % (sample_rate * 10) == 0:
                        print(f"   Frame {frame_count}: {change_type} at {timestamp:.1f}s (score: {change_score:.3f})")
            
            prev_hist = hist
        
        frame_count += 1
    
    cap.release()
    
    print(f"✅ Scene change detection complete: {len(scene_changes)} changes found")
    return scene_changes

def has_scene_change_in_range(scene_changes: List[SceneChange], start_time: float, 
                             end_time: float, min_confidence: float = 0.3) -> bool:
    """Check if there's a scene change in a time range"""
    for change in scene_changes:
        if (start_time <= change.timestamp <= end_time and 
            change.confidence >= min_confidence):
            return True
    return False

def get_scene_change_density(scene_changes: List[SceneChange], start_time: float, 
                            end_time: float) -> float:
    """Calculate scene change density in a time range"""
    if end_time <= start_time:
        return 0.0
    
    changes_in_range = [c for c in scene_changes if start_time <= c.timestamp <= end_time]
    total_time = end_time - start_time
    
    # Weight by confidence and type
    weighted_changes = 0.0
    for change in changes_in_range:
        weight = 1.0
        if change.change_type == "hard_cut":
            weight = 2.0  # Hard cuts are more disruptive
        elif change.change_type == "fade":
            weight = 1.5
        weighted_changes += change.confidence * weight
    
    return weighted_changes / total_time if total_time > 0 else 0.0

def should_avoid_clip_boundary(scene_changes: List[SceneChange], start_time: float, 
                              end_time: float, buffer_seconds: float = 1.0) -> bool:
    """
    Check if a clip boundary should be avoided due to nearby scene changes
    
    Args:
        scene_changes: List of detected scene changes
        start_time: Clip start time
        end_time: Clip end time
        buffer_seconds: Buffer around clip boundaries to avoid
        
    Returns:
        True if clip boundary should be adjusted
    """
    # Check for scene changes near boundaries
    start_buffer = start_time + buffer_seconds
    end_buffer = end_time - buffer_seconds
    
    for change in scene_changes:
        # Avoid scene changes within buffer of start/end
        if (start_time <= change.timestamp <= start_buffer or 
            end_buffer <= change.timestamp <= end_time):
            return True
    
    return False

def suggest_clip_adjustment(scene_changes: List[SceneChange], start_time: float, 
                           end_time: float, buffer_seconds: float = 1.0) -> Tuple[float, float]:
    """
    Suggest adjusted clip boundaries to avoid scene changes
    
    Args:
        scene_changes: List of detected scene changes
        start_time: Original clip start time
        end_time: Original clip end time
        buffer_seconds: Buffer around scene changes to avoid
        
    Returns:
        Tuple of (adjusted_start, adjusted_end)
    """
    adjusted_start = start_time
    adjusted_end = end_time
    
    # Find nearest scene changes
    changes_before_start = [c for c in scene_changes if c.timestamp < start_time]
    changes_after_end = [c for c in scene_changes if c.timestamp > end_time]
    
    if changes_before_start:
        # Find latest scene change before start
        latest_before = max(changes_before_start, key=lambda x: x.timestamp)
        if start_time - latest_before.timestamp < buffer_seconds:
            # Adjust start to be after scene change
            adjusted_start = latest_before.timestamp + buffer_seconds
    
    if changes_after_end:
        # Find earliest scene change after end
        earliest_after = min(changes_after_end, key=lambda x: x.timestamp)
        if earliest_after.timestamp - end_time < buffer_seconds:
            # Adjust end to be before scene change
            adjusted_end = earliest_after.timestamp - buffer_seconds
    
    return adjusted_start, adjusted_end
