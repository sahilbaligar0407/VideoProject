"""
Blur background renderer for ClipGenius Pipeline v2.
Creates blurred background with foreground rectangle overlay.
"""

from typing import List, Tuple, Optional
from .ffmpeg import run_ffmpeg_command, get_common_output_args, build_filter_complex

def render_blur_background(input_path: str, output_path: str, start_time: float, 
                          duration: float, target_width: int = 1080, target_height: int = 1920) -> bool:
    """
    Render blur background layout
    
    Args:
        input_path: Input video path
        output_path: Output video path
        start_time: Start time in seconds
        duration: Duration in seconds
        target_width: Target width
        target_height: Target height
        
    Returns:
        True if successful, False otherwise
    """
    # Build filter complex for blur background
    filters = [
        # Background: scale to target size, blur, crop
        f"[0:v]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
        f"boxblur=40:20,crop={target_width}:{target_height}[bg]",
        
        # Foreground: scale to fit, pad to target size
        f"[0:v]scale={target_width}:-1:force_original_aspect_ratio=decrease,"
        f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2[fgr]",
        
        # Overlay foreground on background
        "[bg][fgr]overlay=0:0,format=yuv420p[outv]"
    ]
    
    filter_complex = build_filter_complex(filters)
    
    # Build FFmpeg command
    cmd = [
        "ffmpeg",
        "-ss", str(start_time),
        "-t", str(duration),
        "-i", input_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a?",
        *get_common_output_args(),
        output_path
    ]
    
    # Run command
    success, output = run_ffmpeg_command(cmd)
    
    if success:
        print(f"✅ Blur background rendered: {output_path}")
    else:
        print(f"❌ Blur background failed: {output}")
    
    return success

def render_blur_background_with_audio(input_path: str, output_path: str, start_time: float,
                                    duration: float, target_width: int = 1080, 
                                    target_height: int = 1920, audio_fade: float = 0.1) -> bool:
    """
    Render blur background with audio fade in/out
    
    Args:
        input_path: Input video path
        output_path: Output video path
        start_time: Start time in seconds
        duration: Duration in seconds
        target_width: Target width
        target_height: Target height
        audio_fade: Audio fade duration in seconds
        
    Returns:
        True if successful, False otherwise
    """
    # Build filter complex for blur background with audio
    filters = [
        # Background: scale to target size, blur, crop
        f"[0:v]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
        f"boxblur=40:20,crop={target_width}:{target_height}[bg]",
        
        # Foreground: scale to fit, pad to target size
        f"[0:v]scale={target_width}:-1:force_original_aspect_ratio=decrease,"
        f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2[fgr]",
        
        # Overlay foreground on background
        "[bg][fgr]overlay=0:0,format=yuv420p[outv]",
        
        # Audio: fade in/out
        f"[0:a]afade=t=in:st=0:d={audio_fade},"
        f"afade=t=out:st={duration-audio_fade}:d={audio_fade}[outa]"
    ]
    
    filter_complex = build_filter_complex(filters)
    
    # Build FFmpeg command
    cmd = [
        "ffmpeg",
        "-ss", str(start_time),
        "-t", str(duration),
        "-i", input_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "[outa]",
        *get_common_output_args(),
        output_path
    ]
    
    # Run command
    success, output = run_ffmpeg_command(cmd)
    
    if success:
        print(f"✅ Blur background with audio rendered: {output_path}")
    else:
        print(f"❌ Blur background with audio failed: {output}")
    
    return success

def render_blur_background_custom_blur(input_path: str, output_path: str, start_time: float,
                                     duration: float, target_width: int = 1080, 
                                     target_height: int = 1920, blur_strength: int = 40) -> bool:
    """
    Render blur background with custom blur strength
    
    Args:
        input_path: Input video path
        output_path: Output video path
        start_time: Start time in seconds
        duration: Duration in seconds
        target_width: Target width
        target_height: Target height
        blur_strength: Blur strength (higher = more blur)
        
    Returns:
        True if successful, False otherwise
    """
    # Build filter complex with custom blur
    filters = [
        # Background: scale to target size, custom blur, crop
        f"[0:v]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
        f"boxblur={blur_strength}:{blur_strength//2},crop={target_width}:{target_height}[bg]",
        
        # Foreground: scale to fit, pad to target size
        f"[0:v]scale={target_width}:-1:force_original_aspect_ratio=decrease,"
        f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2[fgr]",
        
        # Overlay foreground on background
        "[bg][fgr]overlay=0:0,format=yuv420p[outv]"
    ]
    
    filter_complex = build_filter_complex(filters)
    
    # Build FFmpeg command
    cmd = [
        "ffmpeg",
        "-ss", str(start_time),
        "-t", str(duration),
        "-i", input_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a?",
        *get_common_output_args(),
        output_path
    ]
    
    # Run command
    success, output = run_ffmpeg_command(cmd)
    
    if success:
        print(f"✅ Custom blur background rendered: {output_path}")
    else:
        print(f"❌ Custom blur background failed: {output}")
    
    return success

def render_blur_background_with_overlay(input_path: str, output_path: str, start_time: float,
                                      duration: float, target_width: int = 1080, 
                                      target_height: int = 1920, overlay_opacity: float = 0.8) -> bool:
    """
    Render blur background with custom overlay opacity
    
    Args:
        input_path: Input video path
        output_path: Output video path
        start_time: Start time in seconds
        duration: Duration in seconds
        target_width: Target width
        target_height: Target height
        overlay_opacity: Foreground opacity (0-1)
        
    Returns:
        True if successful, False otherwise
    """
    # Build filter complex with custom opacity
    filters = [
        # Background: scale to target size, blur, crop
        f"[0:v]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
        f"boxblur=40:20,crop={target_width}:{target_height}[bg]",
        
        # Foreground: scale to fit, pad to target size, set opacity
        f"[0:v]scale={target_width}:-1:force_original_aspect_ratio=decrease,"
        f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2,"
        f"format=yuva420p,colorchannelmixer=aa={overlay_opacity}[fgr]",
        
        # Overlay foreground on background
        "[bg][fgr]overlay=0:0,format=yuv420p[outv]"
    ]
    
    filter_complex = build_filter_complex(filters)
    
    # Build FFmpeg command
    cmd = [
        "ffmpeg",
        "-ss", str(start_time),
        "-t", str(duration),
        "-i", input_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a?",
        *get_common_output_args(),
        output_path
    ]
    
    # Run command
    success, output = run_ffmpeg_command(cmd)
    
    if success:
        print(f"✅ Blur background with overlay rendered: {output_path}")
    else:
        print(f"❌ Blur background with overlay failed: {output}")
    
    return success
