#!/usr/bin/env python3
"""
Progressive caption state generation for word-by-word building.
Creates caption states that build up to max_words then clear and rebuild.
Implements the "Builder" flow: word1 → word1 word2 → word1 word2 word3 → ... → clear → restart
"""

from typing import List, Dict, Any

def build_progressive_states(
    words: List[Dict[str, Any]],
    max_words: int = 5,
    lead_sec: float = 0.18,
    min_dur_sec: float = 0.12,
    overlap_sec: float = 0.05
) -> List[Dict[str, Any]]:
    """
    For each word i, show window [max(0, i-max_words+1) .. i] as the building line.
    State i starts at words[i].start - lead.
    State i ends at next_word.start + overlap (or words[i].end + 0.10 if last).
    Clamp to min_dur_sec and monotonicity.
    
    Args:
        words: List of word events with start/end times
        max_words: Maximum words per caption before clearing
        lead_sec: Lead time before word start (negative offset)
        min_dur_sec: Minimum duration for each caption state
        overlap_sec: Overlap between consecutive states
        
    Returns:
        List of caption states with progressive text building
    """
    if not words:
        return []

    states = []
    
    for i, w in enumerate(words):
        # Calculate timing for this state
        start = max(0.0, float(w["start"]) - lead_sec)
        
        if i + 1 < len(words):
            # End when next word starts + overlap
            end = float(words[i + 1]["start"]) + overlap_sec
        else:
            # Last state ends when the word ends + small buffer
            end = float(w["end"]) + 0.10
            
        # Ensure minimum duration
        if end - start < min_dur_sec:
            end = start + min_dur_sec

        # Calculate the current block and window
        # Block index determines when to reset (every 5 words)
        block_index = i // max_words
        block_start = block_index * max_words
        
        # Window shows words from block_start up to current word i
        lo = max(0, i - (max_words - 1))
        window = words[lo:i + 1]
        text_tokens = [t["text"] for t in window]

        states.append({
            "start": round(start, 3),
            "end": round(end, 3),
            "text": " ".join(text_tokens),  # Add text field for compatibility
            "tokens": text_tokens,
            "word_count": len(window),
            "block_index": block_index,
            "words": window  # Keep reference to words for styling
        })

    # Make strictly non-overlapping increasing ends (tiny nudges)
    last_end = 0.0
    eps = 0.002
    
    for st in states:
        if st["start"] < last_end:
            st["start"] = round(last_end + eps, 3)
        if st["end"] <= st["start"]:
            st["end"] = round(st["start"] + 0.12, 3)
        last_end = st["end"]
        
    return states
