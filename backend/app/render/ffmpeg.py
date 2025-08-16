"""
FFmpeg helper functions for ClipGenius Pipeline v2.
"""

import subprocess
from typing import List, Dict, Any, Optional, Tuple
import os

def get_common_output_args() -> List[str]:
    """Get common FFmpeg output arguments for consistent encoding"""
    return [
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-crf", "23",
        "-r", "30",
        "-vsync", "cfr",
        "-profile:v", "baseline",
        "-level:v", "3.0",
        "-tag:v", "avc1",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "48000",
        "-ac", "2",
        "-movflags", "+faststart",
        "-y"
    ]

def build_filter_complex(filters: List[str]) -> str:
    """
    Build FFmpeg filter_complex string from list of filters
    
    Args:
        filters: List of filter strings
        
    Returns:
        Combined filter_complex string
    """
    return ";".join(filters)

def run_ffmpeg_command(cmd: List[str], timeout: int = 300) -> Tuple[bool, str]:
    """
    Run FFmpeg command and return success status and output
    
    Args:
        cmd: FFmpeg command as list
        timeout: Command timeout in seconds
        
    Returns:
        Tuple of (success, output/error)
    """
    try:
        print(f"🎬 Running FFmpeg: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        return False, "FFmpeg command timed out"
    except Exception as e:
        return False, f"FFmpeg error: {str(e)}"

def get_video_dimensions(video_path: str) -> Tuple[int, int]:
    """
    Get video dimensions using ffprobe
    
    Args:
        video_path: Path to video file
        
    Returns:
        Tuple of (width, height)
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0",
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # Parse output: width,height
            output = result.stdout.strip()
            if ',' in output:
                width, height = map(int, output.split(','))
                return width, height
    except Exception as e:
        print(f"⚠️ Could not get video dimensions: {e}")
    
    # Fallback to default
    return 1920, 1080

def get_video_duration(video_path: str) -> float:
    """
    Get video duration using ffprobe
    
    Args:
        video_path: Path to video file
        
    Returns:
        Duration in seconds
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            duration = float(result.stdout.strip())
            return duration
    except Exception as e:
        print(f"⚠️ Could not get video duration: {e}")
    
    # Fallback to default
    return 0.0

def validate_video_file(video_path: str) -> bool:
    """
    Validate video file using ffprobe
    
    Args:
        video_path: Path to video file
        
    Returns:
        True if valid, False otherwise
    """
    if not os.path.exists(video_path):
        return False
    
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def create_temp_video_path(base_path: str, suffix: str = "_temp") -> str:
    """
    Create temporary video path
    
    Args:
        base_path: Base video path
        suffix: Suffix to add
        
    Returns:
        Temporary path
    """
    name, ext = os.path.splitext(base_path)
    return f"{name}{suffix}{ext}"

def cleanup_temp_files(temp_paths: List[str]):
    """
    Clean up temporary files
    
    Args:
        temp_paths: List of temporary file paths
    """
    for path in temp_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
                print(f"🧹 Cleaned up: {path}")
        except Exception as e:
            print(f"⚠️ Could not clean up {path}: {e}")

def get_ffmpeg_version() -> str:
    """Get FFmpeg version string"""
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            if lines:
                return lines[0].strip()
    except Exception:
        pass
    
    return "Unknown"

def check_ffmpeg_codecs() -> Dict[str, bool]:
    """
    Check available FFmpeg codecs
    
    Returns:
        Dict of codec availability
    """
    codecs = {}
    
    try:
        result = subprocess.run(["ffmpeg", "-codecs"], capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout.lower()
            codecs = {
                "h264": "h264" in output,
                "libx264": "libx264" in output,
                "aac": "aac" in output,
                "mp3": "mp3" in output
            }
    except Exception:
        pass
    
    return codecs
