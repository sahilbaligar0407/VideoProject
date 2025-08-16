"""
Topic-driven clip search for ClipGenius.
"""

import re
from typing import List, Tuple, Dict, Any
from app.settings import settings
from app.models import HighlightSegment
from app.viral import embed_texts
import numpy as np


def keyword_spans(
    segments: List[Dict[str, Any]], 
    query_words: List[str]
) -> List[Tuple[float, float, float]]:
    """
    Find spans containing keywords with scoring.
    
    Args:
        segments: List of transcript segments
        query_words: List of words to search for
        
    Returns:
        List of (start, end, score) tuples
    """
    if not segments or not query_words:
        return []
    
    # Normalize query words
    query_words = [word.lower().strip() for word in query_words if word.strip()]
    
    # Find segments containing keywords
    keyword_segments = []
    
    for seg in segments:
        seg_text = seg.get('text', '').lower()
        seg_start = seg.get('start', 0)
        seg_end = seg.get('end', 0)
        
        if not seg_text or seg_end <= seg_start:
            continue
        
        # Count keyword matches
        matches = 0
        for word in query_words:
            matches += len(re.findall(r'\b' + re.escape(word) + r'\b', seg_text))
        
        if matches > 0:
            # Score based on frequency and segment length
            segment_duration = seg_end - seg_start
            score = min(1.0, matches / max(1, len(query_words)) * (1.0 / max(0.1, segment_duration)))
            keyword_segments.append((seg_start, seg_end, score))
    
    # Merge overlapping segments
    if not keyword_segments:
        return []
    
    # Sort by start time
    keyword_segments.sort(key=lambda x: x[0])
    
    merged = []
    current_start, current_end, current_score = keyword_segments[0]
    
    for start, end, score in keyword_segments[1:]:
        if start <= current_end:
            # Overlap - merge
            current_end = max(current_end, end)
            current_score = max(current_score, score)
        else:
            # No overlap - save current and start new
            merged.append((current_start, current_end, current_score))
            current_start, current_end, current_score = start, end, score
    
    # Add the last segment
    merged.append((current_start, current_end, current_score))
    
    return merged


async def embedding_spans(
    segments: List[Dict[str, Any]], 
    query_text: str, 
    model: str = None
) -> List[Tuple[float, float, float, str]]:
    """
    Find spans using embedding similarity.
    
    Args:
        segments: List of transcript segments
        query_text: Query text to search for
        model: Embedding model to use
        
    Returns:
        List of (start, end, score, text) tuples
    """
    if not segments or not query_text:
        return []
    
    if model is None:
        model = settings.embedding_model
    
    try:
        # Create rolling windows over transcript
        windows = []
        window_start = 0
        
        for seg in segments:
            seg_start = seg.get('start', 0)
            seg_end = seg.get('end', 0)
            seg_text = seg.get('text', '')
            
            if seg_end <= seg_start or not seg_text:
                continue
            
            # Create overlapping windows
            while window_start < seg_end:
                window_end = min(window_start + settings.topic_window_sec, seg_end)
                
                # Collect text for this window
                window_text = ""
                for s in segments:
                    s_start = s.get('start', 0)
                    s_end = s.get('end', 0)
                    s_text = s.get('text', '')
                    
                    if s_start < window_end and s_end > window_start and s_text:
                        # Calculate overlap
                        overlap_start = max(s_start, window_start)
                        overlap_end = min(s_end, window_end)
                        overlap_duration = overlap_end - overlap_start
                        
                        # Weight text by overlap duration
                        if overlap_duration > 0:
                            window_text += s_text + " "
                
                if window_text.strip():
                    windows.append({
                        'start': window_start,
                        'end': window_end,
                        'text': window_text.strip(),
                        'center': (window_start + window_end) / 2
                    })
                
                window_start += settings.topic_window_sec / 2  # 50% overlap
        
        if not windows:
            return []
        
        # Embed query and window texts
        texts_to_embed = [query_text] + [w['text'] for w in windows]
        embeddings = await embed_texts(texts_to_embed, batch_size=32)
        
        if len(embeddings) != len(texts_to_embed):
            return []
        
        query_embedding = embeddings[0]
        window_embeddings = embeddings[1:]
        
        # Calculate similarities
        similarities = []
        for i, window_embedding in enumerate(window_embeddings):
            # Cosine similarity
            similarity = np.dot(query_embedding, window_embedding)
            similarities.append((i, similarity))
        
        # Sort by similarity and filter by threshold
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, similarity in similarities:
            if similarity >= settings.topic_min_score:
                window = windows[idx]
                results.append((
                    window['start'],
                    window['end'],
                    float(similarity),
                    window['text'][:100] + "..." if len(window['text']) > 100 else window['text']
                ))
        
        return results
        
    except Exception as e:
        print(f"⚠️ Embedding search failed: {e}")
        return []


def topic_windows(
    transcription: Any, 
    query_text: str
) -> List[HighlightSegment]:
    """
    Convert topic search results into HighlightSegments.
    
    Args:
        transcription: Transcription result object
        query_text: Query text to search for
        
    Returns:
        List of HighlightSegment objects
    """
    if not hasattr(transcription, 'segments') or not transcription.segments:
        return []
    
    segments = transcription.segments
    
    # Try keyword search first
    query_words = query_text.lower().split()
    keyword_results = keyword_spans(segments, query_words)
    
    # Convert to HighlightSegments
    highlight_segments = []
    
    for start, end, score in keyword_results:
        # Add padding
        padded_start = max(0, start - settings.topic_window_padding)
        padded_end = min(transcription.duration, end + settings.topic_window_padding)
        
        # Ensure minimum duration
        if padded_end - padded_start < settings.min_clip_duration:
            center = (padded_start + padded_end) / 2
            padded_start = max(0, center - settings.min_clip_duration / 2)
            padded_end = min(transcription.duration, padded_start + settings.min_clip_duration)
        
        # Map score to confidence (0.3-0.8 -> 0.70-0.92)
        confidence = 0.70 + (score - 0.3) * 0.22 / 0.5
        confidence = max(0.70, min(0.92, confidence))
        
        # Create highlight segment
        highlight = HighlightSegment(
            start_time=padded_start,
            end_time=padded_end,
            duration=padded_end - padded_start,
            confidence_score=confidence,
            keywords=["topic_query"],
            transcript_segment=f"Topic: {query_text}",
            detection_method="topic_search"
        )
        
        highlight_segments.append(highlight)
    
    return highlight_segments


async def topic_windows_embedding(
    transcription: Any, 
    query_text: str
) -> List[HighlightSegment]:
    """
    Convert embedding search results into HighlightSegments.
    
    Args:
        transcription: Transcription result object
        query_text: Query text to search for
        
    Returns:
        List of HighlightSegment objects
    """
    if not hasattr(transcription, 'segments') or not transcription.segments:
        return []
    
    segments = transcription.segments
    
    # Use embedding search
    embedding_results = await embedding_spans(segments, query_text)
    
    # Convert to HighlightSegments
    highlight_segments = []
    
    for start, end, score, text in embedding_results:
        # Add padding
        padded_start = max(0, start - settings.topic_window_padding)
        padded_end = min(transcription.duration, end + settings.topic_window_padding)
        
        # Ensure minimum duration
        if padded_end - padded_start < settings.min_clip_duration:
            center = (padded_start + padded_end) / 2
            padded_start = max(0, center - settings.min_clip_duration / 2)
            padded_end = min(transcription.duration, padded_start + settings.min_clip_duration)
        
        # Map score to confidence (0.3-0.8 -> 0.70-0.92)
        confidence = 0.70 + (score - 0.3) * 0.22 / 0.5
        confidence = max(0.70, min(0.92, confidence))
        
        # Create highlight segment
        highlight = HighlightSegment(
            start_time=padded_start,
            end_time=padded_end,
            duration=padded_end - padded_start,
            confidence_score=confidence,
            keywords=["topic_query"],
            transcript_segment=f"Topic: {query_text} (similarity: {score:.3f})",
            detection_method="topic_embedding"
        )
        
        highlight_segments.append(highlight)
    
    return highlight_segments
