"""
Vertical 9:16 video rendering for ClipGenius Pipeline v2.
Integrated with dynamic layout state machine for face-aware rendering.
"""

import os
import subprocess
import random
import json
import math
import tempfile
import cv2  # pip install opencv-python
import numpy as np
from typing import Tuple, Optional, Dict, Any, List
from app.settings import settings
from app.layout.state_machine import LayoutStateMachine, LayoutState, FaceTrack


# ---- helpers ---------------------------------------------------------------

def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0, r

def _ffmpeg_common_outargs():
    return [
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "veryfast", "-crf", "23",
        "-r", "30", "-fps_mode", "cfr",
        "-profile:v", "baseline", "-level:v", "3.0", "-tag:v", "avc1",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
        "-shortest", "-movflags", "+faststart", "-y"
    ]


# ---- LAYOUT 1: full cover crop (no distortion) ----------------------------

def extract_vertical_cover(src, dst, start, duration):
    """Extract vertical 9:16 clip using rock-solid filter chain"""
    # Rock-solid filter: scale to cover 1080x1920, crop exactly, force SAR=1, yuv420p
    fc = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "setsar=1,"
        "format=yuv420p"
    )
    
    cmd = [
        "ffmpeg", "-ss", str(start), "-t", str(duration), "-i", src,
        "-vf", fc,
        "-r", "30",
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-y", dst
    ]
    
    print(f"🎬 Running vertical cover command: {' '.join(cmd)}")
    ok, result = _run(cmd)
    
    if not ok:
        print(f"❌ Vertical cover extraction failed: {result.stderr}")
        # Log first 30 lines of stderr for debugging
        stderr_lines = result.stderr.split('\n')[:30]
        print(f"🔍 First 30 lines of stderr:")
        for line in stderr_lines:
            print(f"   {line}")
        return False
    
    # Verify output dimensions
    if os.path.exists(dst):
        try:
            probe_cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height,sample_aspect_ratio",
                "-of", "csv=p=0", dst
            ]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            if probe_result.returncode == 0:
                output = probe_result.stdout.strip()
                print(f"✅ Vertical cover output verified: {output}")
                return True
            else:
                print(f"⚠️ Could not verify output dimensions: {probe_result.stderr}")
                return True  # Assume success if we can't verify
        except Exception as e:
            print(f"⚠️ Verification failed: {e}")
            return True  # Assume success if verification fails
    
    return False


# ---- LAYOUT 2: podcast face-centered crop ---------------------------------

def extract_podcast_face(src, dst, start, duration, primary_face: Optional[FaceTrack] = None):
    """Extract vertical clip with face-centered crop for podcast content"""
    if primary_face and primary_face.bbox:
        # Use detected face for crop center
        x, y, w, h = primary_face.bbox
        center_x = x + w // 2
        center_y = y + h // 2
        
        # Ensure crop is within bounds and maintains 9:16 aspect ratio
        crop_width = 1080
        crop_height = 1920
        
        # Calculate crop coordinates ensuring we stay within frame bounds
        crop_x = max(0, min(center_x - crop_width // 2, 1920 - crop_width))
        crop_y = max(0, min(center_y - crop_height // 2, 1080 - crop_height))
        
        # Use crop filter for precise face-centered extraction
        fc = (
            f"crop={crop_width}:{crop_height}:{crop_x}:{crop_y},"
            "scale=1080:1920,setsar=1,format=yuv420p"
        )
    else:
        # Fallback to center crop if no face detected
        fc = (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,setsar=1,format=yuv420p"
        )
    
    cmd = [
        "ffmpeg", "-ss", str(start), "-t", str(duration), "-i", src,
        "-vf", fc,
        "-r", "30",
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-y", dst
    ]
    
    print(f"🎬 Running podcast face command: {' '.join(cmd)}")
    ok, result = _run(cmd)
    
    if not ok:
        print(f"❌ Podcast face extraction failed: {result.stderr}")
        return False
    
    return True


# ---- LAYOUT 3: blurred background with foreground rectangle ----------------

def extract_blur_background(src, dst, start, duration):
    """Extract clip with blurred background and foreground rectangle overlay"""
    fc = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,boxblur=40:20,crop=1080:1920,setsar=1[bg];"
        "[0:v]scale=1080:-1:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[fgr];"
        "[bg][fgr]overlay=0:0,format=yuv420p"
    )
    
    cmd = [
        "ffmpeg", "-ss", str(start), "-t", str(duration), "-i", src,
        "-filter_complex", fc,
        "-r", "30",
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-movflags", "+faststart",
        "-y", dst
    ]
    
    print(f"🎬 Running blur background command: {' '.join(cmd)}")
    ok, result = _run(cmd)
    
    if not ok:
        print(f"❌ Blur background extraction failed: {result.stderr}")
        stderr_lines = result.stderr.split('\n')[:30]
        print(f"🔍 First 30 lines of stderr:")
        for line in stderr_lines:
            print(f"   {line}")
        return False
    
    return True


# ---- LAYOUT 4: gameplay background with looping video --------------------

def extract_gameplay_background(src, dst, start, duration, game_bg_path):
    """Extract clip with looping gameplay background and foreground overlay"""
    if not os.path.exists(game_bg_path):
        print(f"⚠️ Game background not found: {game_bg_path}")
        return extract_vertical_cover(src, dst, start, duration)
    
    fc = (
        "[1:v]scale=1080:1920:force_original_aspect_ratio=cover,setsar=1[game];"
        "[0:v]scale=1080:-1:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[fgr];"
        "[game][fgr]overlay=0:0,format=yuv420p"
    )
    
    cmd = [
        "ffmpeg", "-stream_loop", "-1", "-i", game_bg_path,
        "-ss", str(start), "-t", str(duration), "-i", src,
        "-filter_complex", fc,
        "-shortest",
        "-r", "30",
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-movflags", "+faststart",
        "-y", dst
    ]
    
    print(f"🎮 Running gameplay background command: {' '.join(cmd)}")
    ok, result = _run(cmd)
    
    if not ok:
        print(f"❌ Gameplay background extraction failed: {result.stderr}")
        stderr_lines = result.stderr.split('\n')[:30]
        print(f"🔍 First 30 lines of stderr:")
        for line in stderr_lines:
            print(f"   {line}")
        return False
    
    return True


# ---- Dynamic layout rendering with state machine --------------------------

def extract_dynamic_layout(src, dst, start, duration, state_machine: LayoutStateMachine, 
                          background_mode: str = "blur", game_bg_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract vertical clip using dynamic layout switching based on state machine.
    
    Args:
        src: Source video path
        dst: Destination video path
        start: Start time in seconds
        duration: Duration in seconds
        state_machine: Layout state machine instance
        background_mode: "blur" or "gameplay"
        game_bg_path: Path to gameplay background video
        
    Returns:
        Dict with success status and layout information
    """
    print(f"🎬 Dynamic layout extraction: {start:.2f}s to {start + duration:.2f}s")
    
    # Get video info for frame analysis
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"❌ Could not open video: {src}")
        return {"success": False, "error": "Could not open video"}
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Calculate frame range for this clip
    start_frame = int(start * fps)
    end_frame = int((start + duration) * fps)
    
    print(f"📊 Frame range: {start_frame} to {end_frame} (fps: {fps})")
    
    # Analyze frames to determine layout states
    layout_states = []
    current_frame = start_frame
    
    while current_frame < end_frame and current_frame < total_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        ret, frame = cap.read()
        
        if not ret:
            break
        
        # Update state machine with current frame
        state = state_machine.update_state(frame, current_frame, background_mode)
        
        # Get layout configuration
        layout_config = state_machine.get_current_layout_config()
        
        layout_states.append({
            "frame": current_frame,
            "state": state.value,
            "config": layout_config
        })
        
        current_frame += 1
    
    cap.release()
    
    # Determine dominant layout for this clip
    state_counts = {}
    for ls in layout_states:
        state = ls["state"]
        state_counts[state] = state_counts.get(state, 0) + 1
    
    dominant_state = max(state_counts.items(), key=lambda x: x[1])[0]
    print(f"🎯 Dominant layout state: {dominant_state} ({state_counts[dominant_state]} frames)")
    
    # Extract clip using dominant layout
    success = False
    if dominant_state == LayoutState.VERT_FOCUS.value:
        # Find primary face for face-centered crop
        primary_face = None
        for ls in layout_states:
            if ls["state"] == LayoutState.VERT_FOCUS.value and ls["config"]["primary_face"]:
                primary_face = FaceTrack(
                    track_id=ls["config"]["primary_face"]["track_id"],
                    bbox=ls["config"]["primary_face"]["bbox"],
                    confidence=0.8
                )
                break
        
        success = extract_podcast_face(src, dst, start, duration, primary_face)
        
    elif dominant_state == LayoutState.GAMEPLAY.value:
        success = extract_gameplay_background(src, dst, start, duration, game_bg_path)
        
    else:  # BG_BLUR_RECT
        success = extract_blur_background(src, dst, start, duration)
    
    # Get state timeline for manifest
    state_timeline = state_machine.get_state_timeline()
    
    return {
        "success": success,
        "dominant_state": dominant_state,
        "state_counts": state_counts,
        "state_timeline": state_timeline,
        "layout_states": layout_states
    }


# ---- public API ------------------------------------------------------------

def extract_vertical_clip(src, dst, start, duration, mode="cover", theme=None, bg_roots=None):
    """
    mode: "cover" | "podcast_face" | "gaming_template" | "blur_background" | "dynamic"
    theme (gaming): "subway", "templerun", "minecraft" (used to pick bg file)
    bg_roots: dict like {"subway": "assets/bg/subway.mp4", ...}
    """
    print(f"🎬 Extracting vertical clip: mode={mode}, theme={theme}")
    
    if mode == "cover":
        success = extract_vertical_cover(src, dst, start, duration)
        if not success:
            print(f"❌ Vertical cover extraction failed - NOT falling back to standard")
            return False
        return True
        
    elif mode == "podcast_face":
        success = extract_podcast_face(src, dst, start, duration)
        if not success:
            print(f"❌ Podcast face extraction failed - NOT falling back to standard")
            return False
        return True
        
    elif mode == "gaming_template":
        if not bg_roots or not theme or theme not in bg_roots:
            print(f"⚠️ Gaming theme '{theme}' not found in bg_roots, using blur background")
            return extract_blur_background(src, dst, start, duration)
        
        bg_path = bg_roots[theme]
        if not os.path.exists(bg_path):
            print(f"⚠️ Game background file not found: {bg_path}, using blur background")
            return extract_blur_background(src, dst, start, duration)
        
        success = extract_gameplay_background(src, dst, start, duration, bg_path)
        if not success:
            print(f"❌ Gameplay background extraction failed - NOT falling back to standard")
            return False
        return True
        
    elif mode == "blur_background":
        return extract_blur_background(src, dst, start, duration)
        
    elif mode == "dynamic":
        # Dynamic layout requires state machine - this should be called from video processor
        print(f"⚠️ Dynamic mode requires state machine - use extract_dynamic_layout instead")
        return extract_vertical_cover(src, dst, start, duration)
        
    else:
        print(f"⚠️ Unknown mode '{mode}', using cover")
        return extract_vertical_cover(src, dst, start, duration)


# ---- legacy compatibility functions ----------------------------------------

def get_video_dimensions(video_path: str) -> Tuple[int, int]:
    """
    Get video dimensions using ffprobe.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Tuple of (width, height)
    """
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-select_streams", "v:0", video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return 1920, 1080  # Default fallback
        
        data = json.loads(result.stdout)
        if not data.get('streams'):
            return 1920, 1080
        
        stream = data['streams'][0]
        width = int(stream.get('width', 1920))
        height = int(stream.get('height', 1080))
        
        return width, height
        
    except Exception as e:
        print(f"⚠️ Failed to get video dimensions: {e}")
        return 1920, 1080  # Default fallback


def get_vertical_dimensions(width: int = None) -> Tuple[int, int]:
    """
    Get vertical video dimensions based on settings.
    
    Args:
        width: Target width (defaults to settings)
        
    Returns:
        Tuple of (width, height)
    """
    if width is None:
        width = settings.vertical_width
    
    # Use configured height or calculate based on 9:16 aspect ratio
    if hasattr(settings, 'vertical_height'):
        height = settings.vertical_height
    else:
        height = int(width * 16 / 9)
    
    return width, height
