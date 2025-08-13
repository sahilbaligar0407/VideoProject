"""
Similarity computation and caption windowing for viral content detection.
"""

import numpy as np
from typing import List, Dict, Any
from dataclasses import dataclass

from .embeddings import embed_texts
from .viral_vector import get_viral_vector
from ..config import settings


@dataclass
class CaptionWindow:
    """Represents a window of captions for viral scoring."""
    start_time: float
    end_time: float
    text: str
    segments: List[Dict[str, Any]]  # Original segments that fall in this window


@dataclass
class ScoredWindow:
    """A caption window with its viral similarity score."""
    start_time: float
    end_time: float
    score: float
    text: str


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two unit vectors.
    
    Args:
        a: First unit vector
        b: Second unit vector
        
    Returns:
        Cosine similarity score between -1 and 1
    """
    if a.shape != b.shape:
        raise ValueError(f"Vector shapes must match: {a.shape} vs {b.shape}")
    
    # Since vectors are unit-normalized, cosine = dot product
    return float(np.dot(a, b))


def window_captions(segments: List[Dict[str, Any]], 
                   start: float, 
                   end: float, 
                   window_sec: float, 
                   hop_sec: float) -> List[CaptionWindow]:
    """
    Build overlapping windows over captions in the specified time range.
    
    Args:
        segments: List of caption segments with start, end, text
        start: Start time for windowing
        end: End time for windowing
        window_sec: Length of each window in seconds
        hop_sec: Stride between windows in seconds
        
    Returns:
        List of CaptionWindow objects
    """
    if not segments:
        return []
    
    windows = []
    current_start = start
    
    while current_start < end:
        current_end = min(current_start + window_sec, end)
        
        # Find segments that overlap with this window
        window_segments = []
        window_text_parts = []
        
        for segment in segments:
            seg_start = segment.get('start', 0)
            seg_end = segment.get('end', 0)
            seg_text = segment.get('text', '').strip()
            
            # Check if segment overlaps with window
            if seg_end > current_start and seg_start < current_end and seg_text:
                window_segments.append(segment)
                window_text_parts.append(seg_text)
        
        if window_text_parts:
            # Combine text from all segments in this window
            window_text = " ".join(window_text_parts)
            
            # Clean and limit text length
            window_text = " ".join(window_text.split())  # Remove extra whitespace
            if len(window_text) > 300:
                window_text = window_text[:300] + "..."
            
            window = CaptionWindow(
                start_time=current_start,
                end_time=current_end,
                text=window_text,
                segments=window_segments
            )
            windows.append(window)
        
        current_start += hop_sec
    
    return windows


async def score_windows_against_viral_vector(windows: List[CaptionWindow]) -> List[ScoredWindow]:
    """
    Score caption windows against the viral vector using cosine similarity.
    
    Args:
        windows: List of CaptionWindow objects to score
        
    Returns:
        List of ScoredWindow objects sorted by score (descending)
    """
    if not windows:
        return []
    
    # Get the viral vector
    viral_vector, _ = await get_viral_vector()
    
    if viral_vector is None or np.all(viral_vector == 0):
        # No viral vector available, return default scores
        return [ScoredWindow(
            start_time=w.start_time,
            end_time=w.end_time,
            score=0.0,
            text=w.text
        ) for w in windows]
    
    # Extract text from windows for embedding
    window_texts = [w.text for w in windows]
    
    # Get embeddings for all window texts
    embeddings = await embed_texts(window_texts)
    
    if not embeddings or len(embeddings) != len(windows):
        print("⚠️ Failed to get embeddings for windows")
        return []
    
    # Score each window
    scored_windows = []
    for i, (window, embedding) in enumerate(zip(windows, embeddings)):
        if embedding is not None:
            # Compute cosine similarity with viral vector
            score = cosine(embedding, viral_vector)
            
            scored_window = ScoredWindow(
                start_time=window.start_time,
                end_time=window.end_time,
                score=score,
                text=window.text
            )
            scored_windows.append(scored_window)
        else:
            print(f"⚠️ No embedding for window {i}")
    
    # Sort by score (descending)
    scored_windows.sort(key=lambda x: x.score, reverse=True)
    
    return scored_windows


def filter_windows_by_score(windows: List[ScoredWindow], 
                           min_score: float, 
                           top_k: int) -> List[ScoredWindow]:
    """
    Filter scored windows by minimum score and keep top K.
    
    Args:
        windows: List of ScoredWindow objects
        min_score: Minimum score threshold
        top_k: Maximum number of windows to return
        
    Returns:
        Filtered list of ScoredWindow objects
    """
    # Filter by minimum score
    filtered = [w for w in windows if w.score >= min_score]
    
    # Keep top K
    return filtered[:top_k]


def create_highlight_segments_from_windows(windows: List[ScoredWindow], 
                                         video_duration: float,
                                         padding: float = 2.0) -> List[Dict[str, Any]]:
    """
    Convert scored windows to highlight segments for video processing.
    
    Args:
        windows: List of ScoredWindow objects
        video_duration: Total video duration in seconds
        padding: Padding to add before/after each window
        
    Returns:
        List of highlight segment dictionaries
    """
    segments = []
    
    for window in windows:
        # Add padding, clamping to video bounds
        start_time = max(0, window.start_time - padding)
        end_time = min(video_duration, window.end_time + padding)
        
        # Ensure minimum duration
        if end_time - start_time < 5.0:  # At least 5 seconds
            continue
        
        segment = {
            "start_time": start_time,
            "end_time": end_time,
            "confidence_score": 0.7 + 0.3 * window.score,  # Map to 0.7-1.0 range
            "keywords": ["viral_similarity"],
            "text": window.text,
            "viral_score": window.score
        }
        
        segments.append(segment)
    
    return segments
