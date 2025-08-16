"""
Speech detection and segmentation for ClipGenius Pipeline v2.
Reuses existing Whisper transcription data for speech timing.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re

@dataclass
class SpeechSegment:
    """Speech segment with timing and metadata"""
    start: float
    end: float
    text: str
    confidence: float
    speaker_id: Optional[str] = None

def detect_speech_segments(transcription_data: Dict[str, Any]) -> List[SpeechSegment]:
    """
    Extract speech segments from Whisper transcription data
    
    Args:
        transcription_data: Output from OpenAI Whisper API with segments
        
    Returns:
        List of SpeechSegment objects
    """
    segments = []
    
    if not transcription_data or 'segments' not in transcription_data:
        return segments
    
    for segment in transcription_data['segments']:
        if not segment.get('text', '').strip():
            continue
            
        # Extract timing and text
        start = float(segment.get('start', 0))
        end = float(segment.get('end', 0))
        text = segment.get('text', '').strip()
        
        # Skip very short segments (likely noise)
        if end - start < 0.1:
            continue
            
        # Calculate confidence (if available)
        confidence = segment.get('avg_logprob', 0.5) if 'avg_logprob' in segment else 0.5
        
        # Normalize confidence to 0-1 range
        confidence = max(0.0, min(1.0, (confidence + 1.0) / 2.0))
        
        # Extract speaker ID if available (from diarization)
        speaker_id = segment.get('speaker', None)
        
        speech_seg = SpeechSegment(
            start=start,
            end=end,
            text=text,
            confidence=confidence,
            speaker_id=speaker_id
        )
        segments.append(speech_seg)
    
    return segments

def has_speech_in_range(segments: List[SpeechSegment], start_time: float, end_time: float, 
                        min_confidence: float = 0.3) -> bool:
    """Check if there's confident speech in a time range"""
    for segment in segments:
        if (segment.start <= end_time and segment.end >= start_time and 
            segment.confidence >= min_confidence):
            return True
    return False

def get_speech_density(segments: List[SpeechSegment], start_time: float, end_time: float) -> float:
    """Calculate speech density (ratio of time with speech) in a range"""
    if end_time <= start_time:
        return 0.0
    
    speech_time = 0.0
    total_time = end_time - start_time
    
    for segment in segments:
        # Calculate overlap
        seg_start = max(start_time, segment.start)
        seg_end = min(end_time, segment.end)
        
        if seg_end > seg_start:
            speech_time += seg_end - seg_start
    
    return speech_time / total_time if total_time > 0 else 0.0

def detect_speaking_face_overlap(face_boxes: List, speech_segments: List[SpeechSegment], 
                                start_time: float, end_time: float) -> bool:
    """
    Check if there's overlap between face presence and speech in a time range
    
    Args:
        face_boxes: List of FrameBox objects from face tracking
        speech_segments: List of SpeechSegment objects
        start_time: Start of time range
        end_time: End of time range
        
    Returns:
        True if face and speech overlap significantly
    """
    # Get faces in range
    range_faces = [f for f in face_boxes if start_time <= f.t <= end_time]
    
    # Get speech in range
    range_speech = [s for s in speech_segments if s.start <= end_time and s.end >= start_time]
    
    if not range_faces or not range_speech:
        return False
    
    # Calculate overlap
    face_time = len(range_faces) * 0.1  # Assuming 10fps sampling
    speech_time = sum(s.end - s.start for s in range_speech)
    
    # Check if there's significant overlap
    overlap_threshold = 0.3  # 30% overlap required
    return (face_time > 0 and speech_time > 0 and 
            min(face_time, speech_time) / max(face_time, speech_time) > overlap_threshold)

def extract_hook_indicators(segments: List[SpeechSegment], first_n_seconds: float = 5.0) -> Dict[str, Any]:
    """
    Extract hook indicators from the first N seconds of content
    
    Args:
        segments: List of SpeechSegment objects
        first_n_seconds: Look at first N seconds for hooks
        
    Returns:
        Dict with hook indicators and scores
    """
    early_segments = [s for s in segments if s.start < first_n_seconds]
    
    if not early_segments:
        return {"has_hook": False, "score": 0.0, "indicators": []}
    
    # Combine early text
    early_text = " ".join(s.text.lower() for s in early_segments)
    
    # Hook indicators
    interrogatives = ["what", "why", "how", "when", "where", "who", "which", "whose"]
    claims = ["amazing", "incredible", "shocking", "unbelievable", "you won't believe", "this will change"]
    attention = ["listen", "watch", "look", "check out", "you need to see", "important"]
    
    indicators = []
    score = 0.0
    
    # Check for interrogatives
    for word in interrogatives:
        if word in early_text:
            indicators.append(f"interrogative: {word}")
            score += 0.2
    
    # Check for claims
    for phrase in claims:
        if phrase in early_text:
            indicators.append(f"claim: {phrase}")
            score += 0.3
    
    # Check for attention grabbers
    for phrase in attention:
        if phrase in early_text:
            indicators.append(f"attention: {phrase}")
            score += 0.25
    
    # Bonus for multiple indicators
    if len(indicators) > 1:
        score += 0.1
    
    return {
        "has_hook": score > 0.3,
        "score": min(score, 1.0),
        "indicators": indicators
    }
