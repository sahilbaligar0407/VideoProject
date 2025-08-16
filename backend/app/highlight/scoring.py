"""
Enhanced scoring system for ClipGenius Pipeline v2.
Adds speaking-face bonus and hook heuristics to existing scoring.
"""

from typing import List, Dict, Any, Optional
from app.prepass.faces import FrameBox, has_face_in_range
from app.prepass.speech import SpeechSegment, detect_speaking_face_overlap, extract_hook_indicators
from app.models import HighlightSegment

def calculate_enhanced_score(segment: HighlightSegment, face_boxes: List[FrameBox], 
                           speech_segments: List[SpeechSegment], 
                           scene_changes: List = None) -> float:
    """
    Calculate enhanced score with new signals
    
    Args:
        segment: HighlightSegment to score
        face_boxes: List of face detection boxes
        speech_segments: List of speech segments
        scene_changes: List of scene changes (optional)
        
    Returns:
        Enhanced confidence score (0-1)
    """
    base_score = segment.confidence_score
    
    # Calculate bonus signals
    speaking_face_bonus = _calculate_speaking_face_bonus(
        segment, face_boxes, speech_segments
    )
    
    hook_bonus = _calculate_hook_bonus(segment, speech_segments)
    
    # Scene change penalty (if available)
    scene_penalty = 0.0
    if scene_changes:
        scene_penalty = _calculate_scene_change_penalty(segment, scene_changes)
    
    # Combine scores
    enhanced_score = base_score + speaking_face_bonus + hook_bonus - scene_penalty
    
    # Clamp to 0-1 range
    return max(0.0, min(1.0, enhanced_score))

def _calculate_speaking_face_bonus(segment: HighlightSegment, face_boxes: List[FrameBox], 
                                 speech_segments: List[SpeechSegment]) -> float:
    """
    Calculate speaking-face bonus (0.1-0.2)
    
    Bonus when face presence overlaps with speech
    """
    if not face_boxes or not speech_segments:
        return 0.0
    
    # Check for speaking face overlap
    has_overlap = detect_speaking_face_overlap(
        face_boxes, speech_segments, segment.start_time, segment.end_time
    )
    
    if has_overlap:
        # Calculate face presence density
        face_density = _calculate_face_density(face_boxes, segment.start_time, segment.end_time)
        
        # Calculate speech density
        speech_density = _calculate_speech_density(speech_segments, segment.start_time, segment.end_time)
        
        # Bonus based on overlap quality
        overlap_quality = min(face_density, speech_density)
        bonus = 0.1 + (overlap_quality * 0.1)  # 0.1 to 0.2
        
        return bonus
    
    return 0.0

def _calculate_hook_bonus(segment: HighlightSegment, speech_segments: List[SpeechSegment]) -> float:
    """
    Calculate hook bonus (0.05-0.15)
    
    Bonus for early interrogatives/claims in first 5 seconds
    """
    if not speech_segments:
        return 0.0
    
    # Extract hook indicators from early content
    hook_data = extract_hook_indicators(speech_segments, first_n_seconds=5.0)
    
    if hook_data["has_hook"]:
        # Base bonus for having hooks
        base_bonus = 0.05
        
        # Additional bonus based on hook score
        score_bonus = hook_data["score"] * 0.1  # 0 to 0.1
        
        return base_bonus + score_bonus
    
    return 0.0

def _calculate_scene_change_penalty(segment: HighlightSegment, scene_changes: List) -> float:
    """
    Calculate penalty for scene changes near clip boundaries
    
    Returns:
        Penalty value (0-0.1)
    """
    if not scene_changes:
        return 0.0
    
    penalty = 0.0
    buffer_seconds = 1.0  # Buffer around boundaries
    
    for change in scene_changes:
        # Check if scene change is near start
        if abs(change.timestamp - segment.start_time) < buffer_seconds:
            penalty += 0.05 * change.confidence
        
        # Check if scene change is near end
        if abs(change.timestamp - segment.end_time) < buffer_seconds:
            penalty += 0.05 * change.confidence
    
    return min(0.1, penalty)  # Cap penalty at 0.1

def _calculate_face_density(face_boxes: List[FrameBox], start_time: float, end_time: float) -> float:
    """Calculate face presence density in time range"""
    if not face_boxes:
        return 0.0
    
    range_faces = [f for f in face_boxes if start_time <= f.t <= end_time]
    
    if not range_faces:
        return 0.0
    
    # Calculate weighted density (confidence-weighted)
    total_weight = sum(f.conf for f in range_faces)
    total_time = end_time - start_time
    
    return total_weight / total_time if total_time > 0 else 0.0

def _calculate_speech_density(speech_segments: List[SpeechSegment], start_time: float, end_time: float) -> float:
    """Calculate speech density in time range"""
    if not speech_segments:
        return 0.0
    
    speech_time = 0.0
    total_time = end_time - start_time
    
    for segment in speech_segments:
        # Calculate overlap
        seg_start = max(start_time, segment.start)
        seg_end = min(end_time, segment.end)
        
        if seg_end > seg_start:
            speech_time += seg_end - seg_start
    
    return speech_time / total_time if total_time > 0 else 0.0

def apply_enhanced_scoring(segments: List[HighlightSegment], face_boxes: List[FrameBox], 
                          speech_segments: List[SpeechSegment], scene_changes: List = None) -> List[HighlightSegment]:
    """
    Apply enhanced scoring to all segments
    
    Args:
        segments: List of HighlightSegment objects
        face_boxes: List of face detection boxes
        speech_segments: List of speech segments
        scene_changes: List of scene changes (optional)
        
    Returns:
        List of segments with updated confidence scores
    """
    enhanced_segments = []
    
    for segment in segments:
        # Calculate enhanced score
        enhanced_score = calculate_enhanced_score(
            segment, face_boxes, speech_segments, scene_changes
        )
        
        # Create enhanced segment
        enhanced_segment = HighlightSegment(
            start_time=segment.start_time,
            end_time=segment.end_time,
            duration=segment.duration,
            confidence_score=enhanced_score,
            keywords=segment.keywords,
            transcript_segment=segment.transcript_segment,
            detection_method=segment.detection_method
        )
        
        enhanced_segments.append(enhanced_segment)
    
    # Sort by enhanced score
    enhanced_segments.sort(key=lambda x: x.confidence_score, reverse=True)
    
    return enhanced_segments

def get_scoring_breakdown(segment: HighlightSegment, face_boxes: List[FrameBox], 
                         speech_segments: List[SpeechSegment], scene_changes: List = None) -> Dict[str, Any]:
    """
    Get detailed scoring breakdown for a segment
    
    Args:
        segment: HighlightSegment to analyze
        face_boxes: List of face detection boxes
        speech_segments: List of speech segments
        scene_changes: List of scene changes (optional)
        
    Returns:
        Dict with scoring breakdown
    """
    base_score = segment.confidence_score
    
    # Calculate individual components
    speaking_face_bonus = _calculate_speaking_face_bonus(
        segment, face_boxes, speech_segments
    )
    
    hook_bonus = _calculate_hook_bonus(segment, speech_segments)
    
    scene_penalty = 0.0
    if scene_changes:
        scene_penalty = _calculate_scene_change_penalty(segment, scene_changes)
    
    final_score = base_score + speaking_face_bonus + hook_bonus - scene_penalty
    
    return {
        "base_score": base_score,
        "speaking_face_bonus": speaking_face_bonus,
        "hook_bonus": hook_bonus,
        "scene_penalty": scene_penalty,
        "final_score": final_score,
        "face_density": _calculate_face_density(face_boxes, segment.start_time, segment.end_time),
        "speech_density": _calculate_speech_density(speech_segments, segment.start_time, segment.end_time),
        "has_face": has_face_in_range(face_boxes, segment.start_time, segment.end_time),
        "has_speech": any(s.start <= segment.end_time and s.end >= segment.start_time 
                         for s in speech_segments)
    }
