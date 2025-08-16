#!/usr/bin/env python3
"""
Line splitting and word timing for caption rendering.
Handles line breaks, word timing, and enforces 2-line maximum.
"""

from typing import List, Dict, Any
import re

def split_word_timestamps(
    words: List[Dict[str, Any]], 
    max_chars: int = 38, 
    max_duration: float = 2.5, 
    max_gap: float = 1.5
) -> List[Dict[str, Any]]:
    """
    Split words into line segments with proper timing and line breaks.
    
    Args:
        words: List of word dicts with 'word', 'start', 'end' keys
        max_chars: Maximum characters per line
        max_duration: Maximum duration for a single line
        max_gap: Maximum gap between words to keep on same line
    
    Returns:
        List of line segments with timing and word details
    """
    if not words:
        return []
    
    lines = []
    current_line = {
        'start': words[0]['start'],
        'end': words[0]['end'],
        'text': words[0]['word'],
        'words': [words[0]],
        'char_count': len(words[0]['word'])
    }
    
    for i, word in enumerate(words[1:], 1):
        word_text = word['word']
        word_start = word['start']
        word_end = word['end']
        
        # Check if we should start a new line
        should_new_line = False
        
        # Check character count
        if current_line['char_count'] + len(word_text) + 1 > max_chars:
            should_new_line = True
        
        # Check duration
        if word_start - current_line['start'] > max_duration:
            should_new_line = True
        
        # Check gap
        if word_start - current_line['end'] > max_gap:
            should_new_line = True
        
        # Check if we're at 2 lines and need to force a new cue
        if len(lines) >= 2 and should_new_line:
            # Force new cue to maintain 2-line limit
            lines.append(current_line)
            current_line = {
                'start': word_start,
                'end': word_end,
                'text': word_text,
                'words': [word],
                'char_count': len(word_text)
            }
        elif should_new_line:
            # Start new line in current cue
            lines.append(current_line)
            current_line = {
                'start': word_start,
                'end': word_end,
                'text': word_text,
                'words': [word],
                'char_count': len(word_text)
            }
        else:
            # Add to current line
            current_line['text'] += ' ' + word_text
            current_line['end'] = word_end
            current_line['words'].append(word)
            current_line['char_count'] += len(word_text) + 1
    
    # Add the last line
    if current_line:
        lines.append(current_line)
    
    # Ensure we don't exceed 2 lines per cue
    final_lines = []
    current_cue = []
    
    for line in lines:
        if len(current_cue) < 2:
            current_cue.append(line)
        else:
            # Start new cue
            if current_cue:
                final_lines.append(current_cue)
            current_cue = [line]
    
    # Add the last cue
    if current_cue:
        final_lines.append(current_cue)
    
    return final_lines

def split_text_into_words(text: str, start_time: float, end_time: float) -> List[Dict[str, Any]]:
    """
    Split text into words with estimated timing.
    This is a simple implementation - in production you'd use actual word-level timestamps.
    
    Args:
        text: Text to split
        start_time: Start time of the caption
        end_time: End time of the caption
    
    Returns:
        List of word dicts with estimated timing
    """
    words = text.split()
    if not words:
        return []
    
    # Simple timing distribution
    total_duration = end_time - start_time
    word_duration = total_duration / len(words)
    
    word_dicts = []
    for i, word in enumerate(words):
        word_start = start_time + (i * word_duration)
        word_end = word_start + word_duration
        
        word_dicts.append({
            'word': word,
            'start': word_start,
            'end': word_end
        })
    
    return word_dicts

def format_caption_text(lines: List[List[Dict[str, Any]]]) -> str:
    """
    Format caption text for display (e.g., for SRT export).
    
    Args:
        lines: List of line segments from split_word_timestamps
    
    Returns:
        Formatted text with line breaks
    """
    if not lines:
        return ""
    
    # Take the first cue (first 2 lines max)
    first_cue = lines[0]
    
    # Join lines with newline
    return '\n'.join(line['text'] for line in first_cue)
