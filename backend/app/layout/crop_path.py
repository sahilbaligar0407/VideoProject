"""
Crop path builder for ClipGenius Pipeline v2.
Generates smooth face-tracking crop coordinates for FFmpeg auto-reframe.
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from app.prepass.faces import FrameBox

@dataclass
class CropKeyframe:
    """Crop keyframe for FFmpeg"""
    timestamp: float
    x: float          # Center x (0-1 normalized)
    y: float          # Center y (0-1 normalized)
    width: float      # Crop width (0-1 normalized)
    height: float     # Crop height (0-1 normalized)
    zoom: float       # Zoom factor

def build_crop_path(face_boxes: List[FrameBox], src_width: int, src_height: int, 
                   target_aspect: float = 9/16, padding: float = 0.12, 
                   keyframe_rate: int = 10) -> List[CropKeyframe]:
    """
    Build smooth crop path from face tracking data
    
    Args:
        face_boxes: List of FrameBox objects from face tracking
        src_width: Source video width
        src_height: Source video height
        target_aspect: Target aspect ratio (width/height)
        padding: Padding around face (0.12 = 12% padding)
        keyframe_rate: Keyframe rate per second
        
    Returns:
        List of CropKeyframe objects
    """
    if not face_boxes:
        return []
    
    # Calculate target crop dimensions
    if target_aspect > 1:  # Landscape target
        target_width = src_width
        target_height = int(src_width / target_aspect)
    else:  # Portrait target
        target_height = src_height
        target_width = int(src_height * target_aspect)
    
    keyframes = []
    frame_duration = 1.0 / keyframe_rate
    
    # Generate keyframes at regular intervals
    current_time = 0.0
    end_time = max(box.t for box in face_boxes)
    
    while current_time <= end_time:
        # Find face box closest to current time
        closest_box = None
        min_time_diff = float('inf')
        
        for box in face_boxes:
            time_diff = abs(box.t - current_time)
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_box = box
        
        if closest_box and closest_box.conf > 0.3:
            # Calculate crop parameters
            crop_x, crop_y, crop_w, crop_h = _calculate_crop_rect(
                closest_box, src_width, src_height, target_width, target_height, padding
            )
            
            # Normalize coordinates
            norm_x = crop_x / src_width
            norm_y = crop_y / src_height
            norm_w = crop_w / src_width
            norm_h = crop_h / src_height
            
            # Calculate zoom factor
            zoom = min(src_width / crop_w, src_height / crop_h)
            
            keyframe = CropKeyframe(
                timestamp=current_time,
                x=norm_x,
                y=norm_y,
                width=norm_w,
                height=norm_h,
                zoom=zoom
            )
            keyframes.append(keyframe)
        else:
            # No face detected, use center crop
            center_x = 0.5
            center_y = 0.5
            center_w = target_width / src_width
            center_h = target_height / src_height
            
            keyframe = CropKeyframe(
                timestamp=current_time,
                x=center_x,
                y=center_y,
                width=center_w,
                height=center_h,
                zoom=1.0
            )
            keyframes.append(keyframe)
        
        current_time += frame_duration
    
    # Smooth the crop path
    return _smooth_crop_path(keyframes)

def _calculate_crop_rect(face_box: FrameBox, src_width: int, src_height: int,
                        target_width: int, target_height: int, padding: float) -> Tuple[float, float, float, float]:
    """
    Calculate crop rectangle centered on face with padding
    
    Args:
        face_box: Face detection box
        src_width: Source video width
        src_height: Source video height
        target_width: Target crop width
        target_height: Target crop height
        padding: Padding factor around face
        
    Returns:
        Tuple of (x, y, width, height) for crop rectangle
    """
    # Calculate face center
    face_center_x = face_box.x
    face_center_y = face_box.y
    
    # Calculate crop dimensions with padding
    crop_width = face_box.w * (1 + padding)
    crop_height = face_box.h * (1 + padding)
    
    # Ensure crop fits within source dimensions
    crop_width = min(crop_width, src_width)
    crop_height = min(crop_height, src_height)
    
    # Calculate crop position (center on face)
    crop_x = face_center_x - crop_width / 2
    crop_y = face_center_y - crop_height / 2
    
    # Clamp to source bounds
    crop_x = max(0, min(crop_x, src_width - crop_width))
    crop_y = max(0, min(crop_y, src_height - crop_height))
    
    return crop_x, crop_y, crop_width, crop_height

def _smooth_crop_path(keyframes: List[CropKeyframe], smoothing_factor: float = 0.3) -> List[CropKeyframe]:
    """
    Smooth crop path using exponential moving average
    
    Args:
        keyframes: List of CropKeyframe objects
        smoothing_factor: Smoothing factor (0-1, higher = more smoothing)
        
    Returns:
        Smoothed list of CropKeyframe objects
    """
    if len(keyframes) < 2:
        return keyframes
    
    smoothed = [keyframes[0]]  # Keep first keyframe
    
    for i in range(1, len(keyframes)):
        prev = smoothed[-1]
        curr = keyframes[i]
        
        # Smooth all parameters
        smooth_x = _smooth_value(prev.x, curr.x, smoothing_factor)
        smooth_y = _smooth_value(prev.y, curr.y, smoothing_factor)
        smooth_w = _smooth_value(prev.width, curr.width, smoothing_factor)
        smooth_h = _smooth_value(prev.height, curr.height, smoothing_factor)
        smooth_zoom = _smooth_value(prev.zoom, curr.zoom, smoothing_factor)
        
        smooth_keyframe = CropKeyframe(
            timestamp=curr.timestamp,
            x=smooth_x,
            y=smooth_y,
            width=smooth_w,
            height=smooth_h,
            zoom=smooth_zoom
        )
        smoothed.append(smooth_keyframe)
    
    return smoothed

def _smooth_value(prev: float, curr: float, factor: float) -> float:
    """Smooth a single value using exponential moving average"""
    return prev * (1 - factor) + curr * factor

def generate_ffmpeg_crop_filter(keyframes: List[CropKeyframe], src_width: int, src_height: int) -> str:
    """
    Generate FFmpeg crop filter string from keyframes
    
    Args:
        keyframes: List of CropKeyframe objects
        src_width: Source video width
        src_height: Source video height
        
    Returns:
        FFmpeg filter string for crop/zoompan
    """
    if not keyframes:
        return ""
    
    # Generate sendcmd commands for keyframes
    sendcmd_commands = []
    for i, kf in enumerate(keyframes):
        # Convert normalized coordinates to pixel coordinates
        x = kf.x * src_width
        y = kf.y * src_height
        w = kf.width * src_width
        h = kf.height * src_height
        
        # FFmpeg sendcmd format: time command parameter value
        cmd = f"{kf.timestamp:.3f} crop {x:.1f} {y:.1f} {w:.1f} {h:.1f}"
        sendcmd_commands.append(cmd)
    
    # Build filter string
    filter_str = (
        f"sendcmd='{';'.join(sendcmd_commands)}',"
        f"crop='{src_width}:{src_height}:x:y',"
        f"scale=1080:1920"
    )
    
    return filter_str

def export_keyframes_to_file(keyframes: List[CropKeyframe], output_path: str):
    """
    Export keyframes to a file for external processing
    
    Args:
        keyframes: List of CropKeyframe objects
        output_path: Output file path
    """
    with open(output_path, 'w') as f:
        f.write("# Timestamp X Y Width Height Zoom\n")
        for kf in keyframes:
            f.write(f"{kf.timestamp:.3f} {kf.x:.6f} {kf.y:.6f} {kf.width:.6f} {kf.height:.6f} {kf.zoom:.6f}\n")

def load_keyframes_from_file(file_path: str) -> List[CropKeyframe]:
    """
    Load keyframes from a file
    
    Args:
        file_path: Input file path
        
    Returns:
        List of CropKeyframe objects
    """
    keyframes = []
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            
            try:
                parts = line.split()
                if len(parts) >= 6:
                    keyframe = CropKeyframe(
                        timestamp=float(parts[0]),
                        x=float(parts[1]),
                        y=float(parts[2]),
                        width=float(parts[3]),
                        height=float(parts[4]),
                        zoom=float(parts[5])
                    )
                    keyframes.append(keyframe)
            except (ValueError, IndexError):
                continue
    
    return keyframes
