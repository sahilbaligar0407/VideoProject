"""
Smart clip duration and clean ending utilities for ClipGenius.
"""

import numpy as np
import librosa
import subprocess
import json
import os
from typing import Tuple, List, Dict, Any, Optional
from app.settings import settings


def snap_to_transcript_boundary(
    start: float, 
    end: float, 
    segments: List[Dict[str, Any]], 
    max_overhang: float, 
    punctuations: str
) -> Tuple[float, float, str]:
    """
    Find the nearest end-of-sentence boundary at or after the proposed end.
    
    Args:
        start: Start time of the clip
        end: Proposed end time
        segments: List of transcript segments
        max_overhang: Maximum seconds to extend beyond proposed end
        punctuations: String of punctuation characters to look for
        
    Returns:
        Tuple of (new_start, new_end, reason)
    """
    if not segments:
        return start, end, "no_transcript"
    
    # Find segments that overlap with our clip
    clip_segments = [
        seg for seg in segments 
        if seg.get('start', 0) <= end + max_overhang and seg.get('end', 0) >= start
    ]
    
    if not clip_segments:
        return start, end, "no_overlapping_segments"
    
    # Look for punctuation boundaries after the proposed end
    best_end = end
    best_reason = "no_boundary_found"
    
    for seg in clip_segments:
        seg_end = seg.get('end', 0)
        seg_text = seg.get('text', '').strip()
        
        # Check if this segment ends with punctuation
        if seg_text and seg_text[-1] in punctuations:
            # If it's after our proposed end but within overhang limit
            if seg_end > end and seg_end <= end + max_overhang:
                if seg_end > best_end:
                    best_end = seg_end
                    best_reason = f"punctuation_boundary_at_{seg_end:.1f}s"
            
            # If it's before our proposed end, check if it's a better ending
            elif seg_end <= end and seg_end > start + settings.min_clip_duration:
                # Prefer this if it's closer to our target duration
                current_duration = end - start
                new_duration = seg_end - start
                target_duration = settings.target_clip_duration
                
                if abs(new_duration - target_duration) < abs(current_duration - target_duration):
                    best_end = seg_end
                    best_reason = f"better_punctuation_boundary_at_{seg_end:.1f}s"
    
    # Ensure we don't go below minimum duration
    if best_end - start < settings.min_clip_duration:
        best_end = start + settings.min_clip_duration
        best_reason = "enforced_min_duration"
    
    return start, best_end, best_reason


def snap_to_audio_pause(
    audio_path: str, 
    start: float, 
    end: float, 
    thresh_db: float, 
    min_pause: float, 
    max_overhang: float
) -> Tuple[float, float, str]:
    """
    Analyze audio to find a pause near the intended end.
    
    Args:
        audio_path: Path to the audio file
        start: Start time of the clip
        end: Proposed end time
        thresh_db: Silence threshold in dBFS
        min_pause: Required pause duration in seconds
        max_overhang: Maximum seconds to extend beyond proposed end
        
    Returns:
        Tuple of (new_start, new_end, reason)
    """
    try:
        # Load audio around the clip area
        y, sr = librosa.load(audio_path, sr=22050, offset=start, duration=end-start+max_overhang)
        
        if len(y) == 0:
            return start, end, "audio_load_failed"
        
        # Convert to dBFS
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        db = 20 * np.log10(rms + 1e-10)
        
        # Find silence frames (below threshold)
        silence_frames = db < thresh_db
        
        # Look for pauses of minimum duration
        pause_starts = []
        pause_ends = []
        
        in_silence = False
        silence_start = 0
        
        for i, is_silent in enumerate(silence_frames):
            if is_silent and not in_silence:
                silence_start = i
                in_silence = True
            elif not is_silent and in_silence:
                silence_duration = (i - silence_start) * 512 / sr
                if silence_duration >= min_pause:
                    pause_starts.append(silence_start * 512 / sr)
                    pause_ends.append(i * 512 / sr)
                in_silence = False
        
        # Handle case where silence extends to end
        if in_silence:
            silence_duration = (len(silence_frames) - silence_start) * 512 / sr
            if silence_duration >= min_pause:
                pause_starts.append(silence_start * 512 / sr)
                pause_ends.append(len(silence_frames) * 512 / sr)
        
        if not pause_starts:
            return start, end, "no_pauses_found"
        
        # Find the best pause near our proposed end
        best_end = end
        best_reason = "no_suitable_pause"
        
        for pause_start, pause_end in zip(pause_starts, pause_ends):
            pause_center = (pause_start + pause_end) / 2
            
            # If pause is after our proposed end but within overhang limit
            if pause_center > end and pause_center <= end + max_overhang:
                if pause_center > best_end:
                    best_end = pause_center
                    best_reason = f"audio_pause_at_{pause_center:.1f}s"
            
            # If pause is before our proposed end, check if it's better
            elif pause_center <= end and pause_center > start + settings.min_clip_duration:
                current_duration = end - start
                new_duration = pause_center - start
                target_duration = settings.target_clip_duration
                
                if abs(new_duration - target_duration) < abs(current_duration - target_duration):
                    best_end = pause_center
                    best_reason = f"better_audio_pause_at_{pause_center:.1f}s"
        
        # Ensure we don't go below minimum duration
        if best_end - start < settings.min_clip_duration:
            best_end = start + settings.min_clip_duration
            best_reason = "enforced_min_duration"
        
        return start, best_end, best_reason
        
    except Exception as e:
        return start, end, f"audio_analysis_failed: {str(e)}"


def choose_clip_window(
    center: float, 
    duration_policy: Dict[str, float], 
    video_duration: float
) -> Tuple[float, float]:
    """
    Choose optimal clip window centered around highlight.
    
    Args:
        center: Center time of the highlight
        duration_policy: Dictionary with min, target, max durations
        video_duration: Total video duration
        
    Returns:
        Tuple of (start, end)
    """
    min_d = duration_policy.get('min', settings.min_clip_duration)
    target_d = duration_policy.get('target', settings.target_clip_duration)
    max_d = duration_policy.get('max', settings.max_clip_duration)
    
    # Start with target duration
    duration = target_d
    
    # Calculate start and end times
    start = center - duration / 2
    end = center + duration / 2
    
    # Clamp to video boundaries
    if start < 0:
        start = 0
        end = min(duration, video_duration)
    elif end > video_duration:
        end = video_duration
        start = max(0, video_duration - duration)
    
    # Ensure minimum duration
    if end - start < min_d:
        if start == 0:
            end = min(min_d, video_duration)
        elif end == video_duration:
            start = max(0, video_duration - min_d)
        else:
            # Center the clip
            center = (start + end) / 2
            start = max(0, center - min_d / 2)
            end = min(video_duration, start + min_d)
            start = max(0, end - min_d)
    
    # Ensure maximum duration
    if end - start > max_d:
        center = (start + end) / 2
        start = center - max_d / 2
        end = center + max_d / 2
        
        # Re-clamp to boundaries
        if start < 0:
            start = 0
            end = max_d
        elif end > video_duration:
            end = video_duration
            start = video_duration - max_d
    
    return start, end


def duration_preference(duration: float, target: float, min_d: float, max_d: float) -> float:
    """
    Calculate duration preference score using triangular distribution.
    
    Args:
        duration: Clip duration
        target: Target duration
        min_d: Minimum duration
        max_d: Maximum duration
        
    Returns:
        Score between 0.6 and 1.0
    """
    if duration < min_d or duration > max_d:
        return 0.6
    
    # Linearly ramp from min->target and target->max
    if duration <= target:
        return 0.6 + 0.4 * (duration - min_d) / max(1e-6, (target - min_d))
    else:
        return 1.0 - 0.4 * (duration - target) / max(1e-6, (max_d - target))
