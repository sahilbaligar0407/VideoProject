"""
Auto-reframe renderer for ClipGenius Pipeline v2.
Handles face-tracking crop paths and smooth transitions.
"""

from typing import List, Tuple, Optional
from .ffmpeg import run_ffmpeg_command, get_common_output_args, build_filter_complex

def render_auto_reframe(
    input_path: str,
    output_path: str,
    start_time: float,
    duration: float,
    crop_keyframes: List,
    target_width: int = 1080,
    target_height: int = 1920
) -> bool:
    """
    Render auto-reframe clip with face-tracking crop path.
    
    Args:
        input_path: Path to input video
        output_path: Path for output video
        start_time: Start time in seconds
        duration: Clip duration in seconds
        crop_keyframes: List of crop keyframes with timing and coordinates
        target_width: Output width
        target_height: Output height
        
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"🎯 Rendering auto-reframe clip with {len(crop_keyframes)} keyframes")
        
        if not crop_keyframes:
            print("⚠️ No crop keyframes provided, using center crop")
            return _render_center_crop(input_path, output_path, start_time, duration, target_width, target_height)
        
        # Create crop filter with keyframes
        crop_filter = _build_crop_filter(crop_keyframes, target_width, target_height)
        
        filters = [
            f"[0:v]trim=start={start_time}:duration={duration},{crop_filter},scale={target_width}:{target_height}[out]"
        ]
        
        filter_complex = build_filter_complex(filters)
        
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-map", "0:a",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            *get_common_output_args(),
            output_path
        ]
        
        success, output = run_ffmpeg_command(cmd)
        
        if success:
            print(f"✅ Auto-reframe rendered successfully")
            return True
        else:
            print(f"❌ Auto-reframe rendering failed: {output}")
            return False
            
    except Exception as e:
        print(f"❌ Auto-reframe rendering failed: {e}")
        return False

def _build_crop_filter(keyframes: List, target_width: int, target_height: int) -> str:
    """Build FFmpeg crop filter string from keyframes."""
    if not keyframes:
        return f"crop={target_width}:{target_height}"
    
    # For now, use the first keyframe as static crop
    # In a full implementation, this would create a dynamic crop path
    first_keyframe = keyframes[0]
    
    # Calculate crop dimensions based on keyframe
    crop_width = int(first_keyframe.get('width', 1.0) * target_width)
    crop_height = int(first_keyframe.get('height', 1.0) * target_height)
    crop_x = int(first_keyframe.get('x', 0.5) * target_width - crop_width // 2)
    crop_y = int(first_keyframe.get('y', 0.5) * target_height - crop_height // 2)
    
    return f"crop={crop_width}:{crop_height}:{crop_x}:{crop_y}"

def _render_center_crop(
    input_path: str,
    output_path: str,
    start_time: float,
    duration: float,
    target_width: int,
    target_height: int
) -> bool:
    """Render center crop as fallback."""
    try:
        filters = [
            f"[0:v]trim=start={start_time}:duration={duration},crop={target_width}:{target_height},scale={target_width}:{target_height}[out]"
        ]
        
        filter_complex = build_filter_complex(filters)
        
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-map", "0:a",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            *get_common_output_args(),
            output_path
        ]
        
        success, output = run_ffmpeg_command(cmd)
        return success
        
    except Exception as e:
        print(f"❌ Center crop rendering failed: {e}")
        return False

def render_auto_reframe_with_smoothing(
    input_path: str,
    output_path: str,
    start_time: float,
    duration: float,
    crop_keyframes: List,
    target_width: int = 1080,
    target_height: int = 1920,
    smoothing_factor: float = 0.3
) -> bool:
    """
    Render auto-reframe with additional smoothing.
    
    Args:
        input_path: Path to input video
        output_path: Path for output video
        start_time: Start time in seconds
        duration: Clip duration in seconds
        crop_keyframes: List of crop keyframes
        target_width: Output width
        target_height: Output height
        smoothing_factor: Smoothing factor (0.0 to 1.0)
        
    Returns:
        True if successful, False otherwise
    """
    # For now, fall back to regular auto-reframe
    # Smoothing would be implemented in a full version
    print(f"⚠️ Smoothing not yet implemented, using regular auto-reframe")
    return render_auto_reframe(
        input_path, output_path, start_time, duration,
        crop_keyframes, target_width, target_height
    )
