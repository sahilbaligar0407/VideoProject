"""
Transition renderer for ClipGenius Pipeline v2.
Handles scene transitions and effects between clips.
"""

from typing import List, Tuple, Optional
from .ffmpeg import run_ffmpeg_command, get_common_output_args, build_filter_complex

def render_transition(
    input_path: str,
    output_path: str,
    start_time: float,
    duration: float,
    transition_type: str = "fade",
    transition_duration: float = 0.5,
    target_width: int = 1080,
    target_height: int = 1920
) -> bool:
    """
    Render clip with transition effect.
    
    Args:
        input_path: Path to input video
        output_path: Path for output video
        start_time: Start time in seconds
        duration: Clip duration in seconds
        transition_type: Type of transition (fade, zoom, slide)
        transition_duration: Duration of transition effect
        target_width: Output width
        target_height: Output height
        
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"🎬 Rendering {transition_type} transition")
        
        if transition_type == "fade":
            return _render_fade_transition(
                input_path, output_path, start_time, duration,
                transition_duration, target_width, target_height
            )
        elif transition_type == "zoom":
            return _render_zoom_transition(
                input_path, output_path, start_time, duration,
                transition_duration, target_width, target_height
            )
        elif transition_type == "slide":
            return _render_slide_transition(
                input_path, output_path, start_time, duration,
                transition_duration, target_width, target_height
            )
        else:
            print(f"⚠️ Unknown transition type: {transition_type}, using fade")
            return _render_fade_transition(
                input_path, output_path, start_time, duration,
                transition_duration, target_width, target_height
            )
            
    except Exception as e:
        print(f"❌ Transition rendering failed: {e}")
        return False

def _render_fade_transition(
    input_path: str,
    output_path: str,
    start_time: float,
    duration: float,
    transition_duration: float,
    target_width: int,
    target_height: int
) -> bool:
    """Render fade in/out transition."""
    try:
        # Create fade in and fade out effects
        fade_in_duration = min(transition_duration, duration / 2)
        fade_out_duration = min(transition_duration, duration / 2)
        
        filters = [
            f"[0:v]trim=start={start_time}:duration={duration},"
            f"fade=t=in:st=0:d={fade_in_duration},"
            f"fade=t=out:st={duration-fade_out_duration}:d={fade_out_duration},"
            f"scale={target_width}:{target_height}[out]"
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
            print(f"✅ Fade transition rendered successfully")
            return True
        else:
            print(f"❌ Fade transition rendering failed: {output}")
            return False
            
    except Exception as e:
        print(f"❌ Fade transition rendering failed: {e}")
        return False

def _render_zoom_transition(
    input_path: str,
    output_path: str,
    start_time: float,
    duration: float,
    transition_duration: float,
    target_width: int,
    target_height: int
) -> bool:
    """Render zoom in/out transition."""
    try:
        # Create zoom in and zoom out effects
        zoom_in_duration = min(transition_duration, duration / 2)
        zoom_out_duration = min(transition_duration, duration / 2)
        
        filters = [
            f"[0:v]trim=start={start_time}:duration={duration},"
            f"zoompan=z='if(lte(on,{zoom_in_duration}),1+{zoom_in_duration-on}/{zoom_in_duration}*0.3,if(gte(on,{duration-zoom_out_duration}),1+{on-{duration-zoom_out_duration}}/{zoom_out_duration}*0.3,1))':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',"
            f"scale={target_width}:{target_height}[out]"
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
            print(f"✅ Zoom transition rendered successfully")
            return True
        else:
            print(f"❌ Zoom transition rendering failed: {output}")
            return False
            
    except Exception as e:
        print(f"❌ Zoom transition rendering failed: {e}")
        return False

def _render_slide_transition(
    input_path: str,
    output_path: str,
    start_time: float,
    duration: float,
    transition_duration: float,
    target_width: int,
    target_height: int
) -> bool:
    """Render slide in/out transition."""
    try:
        # Create slide in and slide out effects
        slide_in_duration = min(transition_duration, duration / 2)
        slide_out_duration = min(transition_duration, duration / 2)
        
        filters = [
            f"[0:v]trim=start={start_time}:duration={duration},"
            f"crop={target_width}:{target_height},"
            f"pad={target_width}:{target_height}:0:0:color=black,"
            f"overlay=x='if(lte(on,{slide_in_duration}),{target_width}-{target_width}*on/{slide_in_duration},if(gte(on,{duration-slide_out_duration}),{target_width}*{on-{duration-slide_out_duration}}/{slide_out_duration},0))':y=0[out]"
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
            print(f"✅ Slide transition rendered successfully")
            return True
        else:
            print(f"❌ Slide transition rendering failed: {output}")
            return False
            
    except Exception as e:
        print(f"❌ Slide transition rendering failed: {e}")
        return False

def get_available_transitions() -> List[str]:
    """Get list of available transition types."""
    return ["fade", "zoom", "slide", "none"]

def validate_transition_type(transition_type: str) -> bool:
    """Validate if a transition type is supported."""
    return transition_type in get_available_transitions()
