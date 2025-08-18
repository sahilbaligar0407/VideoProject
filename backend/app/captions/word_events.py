#!/usr/bin/env python3
"""
Word-level event processing for progressive caption generation.
Flattens Whisper segments into individual word events with precise timing.
Includes all speakers with safe clip range and fallback handling.
"""

import re
from typing import List, Dict, Any

# Punctuation pattern for token cleaning
PUNCT = re.compile(r"[^\w'\-]+", re.UNICODE)

def _clean_token(tok: str) -> str:
    """Clean token by removing problematic punctuation"""
    return PUNCT.sub("", tok or "").strip()

def flatten_word_events(
    segments: List[Dict[str, Any]], 
    clip_start_abs: float, 
    clip_end_abs: float, 
    pad_head: float = 0.25, 
    pad_tail: float = 0.25
) -> List[Dict[str, Any]]:
    """
    Return words across ALL speakers, time-sorted, clip-relative.
    Keeps words whose absolute start is in [clip_start_abs-pad_head, clip_end_abs+pad_tail].
    
    Args:
        segments: Whisper segments with optional words array
        clip_start_abs: Absolute start time of the clip
        clip_end_abs: Absolute end time of the clip
        pad_head: Head padding to avoid dropping fast words
        pad_tail: Tail padding to avoid dropping fast words
        
    Returns:
        List of word events: {"text": "word", "start": float, "end": float}
        Times are clip-relative, sorted by start time
    """
    words = []
    if not segments:
        return words

    # Define safe time window with padding
    lo = max(0.0, clip_start_abs - pad_head)
    hi = clip_end_abs + pad_tail

    for seg in segments:
        wlist = seg.get("words") or []
        
        # If no word timing, fall back to the whole segment split (rare)
        if not wlist and seg.get("text"):
            # Naive split with even distribution
            text = seg["text"]
            toks = [t for t in re.split(r"\s+", text) if t]
            
            if seg.get("start") is None or seg.get("end") is None or len(toks) == 0:
                continue
                
            dur = max(0.06, float(seg["end"]) - float(seg["start"]))
            step = dur / max(1, len(toks))
            
            for i, tok in enumerate(toks):
                s = float(seg["start"]) + i * step
                e = min(float(seg["end"]), s + max(0.06, step))
                
                # Skip if outside safe window
                if e < lo or s > hi:
                    continue
                    
                words.append({"text": tok, "start": s, "end": e})
            continue

        # Process words with timing
        for w in wlist:
            s = float(w.get("start", seg.get("start", 0.0)))
            e = float(w.get("end", seg.get("end", s + 0.12)))
            
            # Skip if outside safe window
            if e < lo or s > hi:
                continue
                
            tok = _clean_token(w.get("word", w.get("text", "")))
            if not tok:
                continue
                
            words.append({"text": tok, "start": s, "end": e})

    # Sort by start time, then end time
    words.sort(key=lambda x: (x["start"], x["end"]))
    
    # Convert to clip-relative times
    for w in words:
        w["start"] = max(0.0, w["start"] - clip_start_abs)
        w["end"] = max(w["start"] + 0.06, w["end"] - clip_start_abs)  # Ensure min duration
        
    return words
