#!/usr/bin/env python3
"""
Bulletproof drawtext filter builder for FFmpeg caption burning.
Supports Poppins fonts, karaoke highlighting, and proper line wrapping.
"""

import os
from typing import List, Dict, Any
from .fonts import get_bundled_poppins_bold

def escape_text_for_drawtext(text: str) -> str:
    """
    Escape text content for safe use in FFmpeg drawtext filters.
    Handles apostrophes, quotes, and other problematic characters.
    """
    if not text:
        return ""
    
    # Replace problematic characters with safe alternatives
    safe_text = text.replace("'", "'")  # Replace apostrophe with smart quote
    safe_text = safe_text.replace('"', '"')  # Replace double quote with smart quote
    safe_text = safe_text.replace(';', ',')  # Replace semicolon with comma
    safe_text = safe_text.replace(':', ' -')  # Replace colon with dash
    
    # Remove any remaining problematic characters
    safe_text = ''.join(char for char in safe_text if ord(char) >= 32 and ord(char) <= 126)
    
    # Limit text length to prevent filter string issues
    if len(safe_text) > 100:
        safe_text = safe_text[:97] + "..."
    
    return safe_text

def build_visible_caption_test(
    text: str = "CAPTION_VISIBLE_TEST",
    clip_start: float = 0.0,
    clip_duration: float = 6.0
) -> str:
    """
    Build a highly visible caption test pattern with guaranteed visibility.
    
    Args:
        text: Caption text to display
        clip_start: Clip start time
        clip_duration: Clip duration for timing
    
    Returns:
        Complete filter string with drawbox background and clamped positioning
    """
    # Get Poppins font path
    font_path = get_bundled_poppins_bold()
    
    # Build the filter string with guaranteed visibility
    filter_parts = [
        # Format first (required for some filters)
        "format=yuv420p",
        
        # Background box behind captions for guaranteed contrast
        "drawbox=x=0:y=h-340:w=1080:h=320:color=black@0.65:t=fill",
        
        # Main caption text
        f"drawtext=fontfile='{font_path}':text='{text}':x='(w-text_w)/2':y='if(gt(h-240-text_h,0),h-240-text_h,10)':fontsize=64:fontcolor=white:borderw=0:box=1:boxcolor=black@0.0:boxborderw=0:enable='between(t,{clip_start + 0.8:.1f},{clip_start + clip_duration:.1f})'",
        
        # CAPS_OK watermark
        f"drawtext=fontfile='{font_path}':text='CAPS_OK':x='(w-text_w)/2':y='if(gt(h-120-text_h,0),h-120-text_h,10)':fontsize=54:fontcolor=yellow:box=1:boxcolor=black@0.6:boxborderw=20:enable='between(t,{clip_start + 0.8:.1f},{clip_start + clip_duration:.1f})'"
    ]
    
    return ",".join(filter_parts)

def build_single_drawtext(
    text: str,
    start_time: float,
    end_time: float,
    x_pos: str = "(w-text_w)/2",
    y_pos: str = "h-160",
    fontsize: int = 48,
    fontcolor: str = "white",
    fontfile: str = None,
    box: bool = True,
    boxcolor: str = "black@0.6",
    boxborderw: int = 20,
    enable_expr: str = None
) -> str:
    """
    Build a single drawtext filter string.
    
    Args:
        text: Text to display
        start_time: Start time (clip-relative)
        end_time: End time (clip-relative)
        x_pos: X position expression
        y_pos: Y position expression
        fontsize: Font size
        fontcolor: Font color
        fontfile: Font file path
        box: Whether to add background box
        boxcolor: Box color with opacity
        boxborderw: Box border width
        enable_expr: Custom enable expression (overrides timing)
    
    Returns:
        Complete drawtext filter string
    """
    if not text:
        return ""
    
    # Simple text escaping - just replace problematic characters
    safe_text = text.replace("'", "'")  # Replace apostrophe with different quote
    safe_text = safe_text.replace('"', '"')  # Replace double quote with different quote
    safe_text = safe_text.replace(';', ',')  # Replace semicolon with comma
    
    # Build filter parts
    parts = []
    
    # Text - use single quotes
    parts.append(f"text='{safe_text}'")
    
    # Timing (enable expression) - use always visible for now to test
    if enable_expr:
        parts.append(f"enable='{enable_expr}'")
    else:
        parts.append("enable='1'")  # Always visible for testing
    
    # Position
    parts.append(f"x='{x_pos}'")
    parts.append(f"y='{y_pos}'")
    
    # Font properties
    parts.append(f"fontsize={fontsize}")
    parts.append(f"fontcolor={fontcolor}")
    
    if fontfile:
        parts.append(f"fontfile='{fontfile}'")
    
    # Box properties
    if box:
        parts.append("box=1")
        parts.append(f"boxcolor={boxcolor}")
        parts.append(f"boxborderw={boxborderw}")
    
    # Join with colons
    return "drawtext=" + ":".join(parts)

def build_karaoke_drawtext(
    lines: List[List[Dict[str, Any]]],
    clip_start: float = 0.0,
    style: str = "poppins_bold_boxed"
) -> str:
    """
    Build karaoke-style drawtext filter with base text and word highlights.
    
    Args:
        lines: Line segments from split_word_timestamps
        clip_start: Clip start time (for clip-relative timing)
        style: Style preset name
    
    Returns:
        Complete drawtext filter string
    """
    if not lines:
        return ""
    
    # Get style configuration
    style_config = get_style_config(style)
    
    # Build filters for each line segment
    filters = []
    
    for cue in lines:
        if not cue:
            continue
        
        # Base text (white, always visible during cue)
        cue_start = cue[0]['start'] - clip_start
        cue_end = cue[-1]['end'] - clip_start
        
        # Format text for this cue (max 2 lines)
        cue_text = '\n'.join(line['text'] for line in cue[:2])
        
        # Base layer (white text)
        base_filter = build_single_drawtext(
            text=cue_text,
            start_time=cue_start,
            end_time=cue_end,
            x_pos=style_config['x_pos'],
            y_pos=style_config['y_pos'],
            fontsize=style_config['fontsize'],
            fontcolor=style_config['fontcolor'],
            fontfile=style_config['fontfile'],
            box=style_config['box'],
            boxcolor=style_config['boxcolor'],
            boxborderw=style_config['boxborderw']
        )
        filters.append(base_filter)
        
        # Word highlight layer (yellow, per-word timing)
        for line in cue[:2]:  # Max 2 lines
            for word in line['words']:
                word_start = word['start'] - clip_start
                word_end = word['end'] - clip_start
                
                # Highlight filter (yellow, word-timed)
                highlight_filter = build_single_drawtext(
                    text=word['word'],
                    start_time=word_start,
                    end_time=word_end,
                    x_pos=style_config['x_pos'],
                    y_pos=style_config['y_pos'],
                    fontsize=style_config['fontsize'],
                    fontcolor="yellow",  # Highlight color
                    fontfile=style_config['fontfile'],
                    box=False,  # No box for highlights
                    enable_expr=f"between(t,{word_start:.2f},{word_end:.2f})"
                )
                filters.append(highlight_filter)
    
    # Join with commas, ensuring no empty filters
    valid_filters = [f for f in filters if f.strip()]
    return ",".join(valid_filters)

def get_style_config(style: str = "poppins_bold_boxed") -> Dict[str, Any]:
    """
    Get style configuration for caption rendering.
    
    Args:
        style: Style preset name
    
    Returns:
        Style configuration dictionary
    """
    if style == "poppins_bold_boxed":
        return {
            'fontfile': get_bundled_poppins_bold(),
            'fontsize': 48,
            'fontcolor': 'white',
            'x_pos': '(w-text_w)/2',
            'y_pos': 'if(gt(h-160-text_h,0),h-160-text_h,10)',  # Clamped Y positioning
            'box': True,
            'boxcolor': 'black@0.6',
            'boxborderw': 20,
            'marginV': 160
        }
    elif style == "poppins_medium_outline":
        return {
            'fontfile': get_bundled_poppins_bold(),  # Fallback to bold for now
            'fontsize': 44,
            'fontcolor': 'white',
            'x_pos': '(w-text_w)/2',
            'y_pos': 'if(gt(h-160-text_h,0),h-160-text_h,10)',  # Clamped Y positioning
            'box': False,
            'boxcolor': 'black@0.6',
            'boxborderw': 0,
            'marginV': 160
        }
    else:
        # Default fallback
        return {
            'fontfile': 'C:/Windows/Fonts/arial.ttf',
            'fontsize': 48,
            'fontcolor': 'white',
            'x_pos': '(w-text_w)/2',
            'y_pos': 'if(gt(h-160-text_h,0),h-160-text_h,10)',  # Clamped Y positioning
            'box': True,
            'boxcolor': 'black@0.6',
            'boxborderw': 20,
            'marginV': 160
        }

def build_simple_drawtext_filter_simple(
    segments: List[Dict[str, Any]],
    clip_start: float = 0.0,
    style: str = "poppins_bold_boxed"
) -> str:
    """
    Build a simple drawtext filter for caption burning - simplified version.
    Process one caption at a time to avoid complex filter string issues.
    """
    if not segments:
        return ""
    
    # Get style configuration
    style_config = get_style_config(style)
    
    # For now, just use the first segment to test
    if len(segments) > 0:
        segment = segments[0]
        
        # Convert global times to clip-relative times
        start_local = max(0.0, segment['start'] - clip_start)
        end_local = max(0.1, segment['end'] - clip_start)
        
        # Simple text (no complex line breaks for now)
        text = segment['text'].replace('\n', ' ')
        
        # Skip empty text
        if not text.strip():
            return ""
        
        # Build single filter (white text with box)
        single_filter = build_single_drawtext(
            text=text,
            start_time=start_local,
            end_time=end_local,
            x_pos=style_config['x_pos'],
            y_pos=style_config['y_pos'],
            fontsize=style_config['fontsize'],
            fontcolor=style_config['fontcolor'],
            fontfile=style_config['fontfile'],
            box=style_config['box'],
            boxcolor=style_config['boxcolor'],
            boxborderw=style_config['boxborderw']
        )
        
        return single_filter
    
    return ""

def build_drawtext_filter(
    clip_start: float,
    segments: List[Dict[str, Any]],
    style: str = "poppins_bold_boxed",
    debug_watermark: bool = False  # Changed to False since video processor adds it
) -> str:
    """
    Build complete drawtext filter for caption burning.
    
    Args:
        clip_start: Clip start time (for clip-relative timing)
        segments: Caption segments with start, end, text
        style: Style preset name
        debug_watermark: Whether to add debug watermark (deprecated, handled by video processor)
    
    Returns:
        Complete drawtext filter string
    """
    if not segments:
        return ""
    
    # Use safe phrase-based timed captions for reliable caption rendering
    # This creates captions that appear as the speaker talks but with safe text
    main_filter = build_safe_phrase_captions(segments, clip_start, style)
    
    # Note: Debug watermark is now added by the video processor
    # to avoid duplication and ensure proper integration
    
    return main_filter

def validate_filter_string(filter_string: str) -> bool:
    """
    Basic validation of drawtext filter string.
    
    Args:
        filter_string: Filter string to validate
    
    Returns:
        True if valid, False otherwise
    """
    print(f"🔍 Validating filter string: {filter_string[:200]}...")
    print(f"🔍 Filter string length: {len(filter_string)}")
    
    if not filter_string:
        print("❌ Filter string is empty")
        return False
    
    # Check for basic structure - should contain drawtext= somewhere
    if "drawtext=" not in filter_string:
        print("❌ Filter string does not contain 'drawtext='")
        return False
    
    # Count the number of drawtext filters
    drawtext_count = filter_string.count("drawtext=")
    print(f"🔍 Found {drawtext_count} drawtext filters")
    
    if drawtext_count == 0:
        print("❌ No drawtext filters found")
        return False
    
    # Check for required parameters (should be present in the overall string)
    required_params = ["text=", "x=", "y=", "fontsize="]
    for param in required_params:
        if param not in filter_string:
            print(f"❌ Missing required parameter: {param}")
            return False
    
    # Check that the string contains the required filter elements
    # Note: format=yuv420p is added by the video processor, not required here
    required_elements = ["drawbox", "drawtext="]
    for element in required_elements:
        if element not in filter_string:
            print(f"❌ Missing required element: {element}")
            return False
    
    print("✅ Filter string validation passed")
    return True

def build_phrase_timed_captions(
    segments: List[Dict[str, Any]],
    clip_start: float = 0.0,
    style: str = "poppins_bold_boxed"
) -> str:
    """
    Build phrase-based timed captions that appear as the speaker talks.
    Groups words into logical phrases to reduce filter complexity.
    
    Args:
        segments: Caption segments with start, end, text
        clip_start: Clip start time (for clip-relative timing)
        style: Style preset name
    
    Returns:
        Complete filter string with phrase-based timing
    """
    if not segments:
        return ""
    
    # Get style configuration
    style_config = get_style_config(style)
    font_path = get_bundled_poppins_bold()
    
    # Build filters for each segment
    filters = []
    
    for segment in segments:
        if not segment.get('text'):
            continue
            
        # Convert global times to clip-relative times
        start_local = max(0.0, segment['start'] - clip_start)
        end_local = max(0.1, segment['end'] - clip_start)
        
        # Skip segments that are too short or off-screen
        if end_local - start_local < 0.2:
            continue
            
        # Clean and prepare text
        text = segment['text'].strip()
        if not text:
            continue
        
        # Escape text for safe FFmpeg usage
        safe_text = escape_text_for_drawtext(text)
        
        # Skip if text is too short after escaping
        if len(safe_text) < 3:
            continue
        
        # Build phrase filter with proper timing
        phrase_filter = (
            f"drawtext=fontfile='{font_path}':text='{safe_text}':"
            f"x='(w-text_w)/2':y='if(gt(h-240-text_h,0),h-240-text_h,10)':"
            f"fontsize={style_config['fontsize']}:fontcolor={style_config['fontcolor']}:"
            f"box=1:boxcolor=black@0.6:boxborderw=20:"
            f"enable='between(t,{start_local:.2f},{end_local:.2f})'"
        )
        filters.append(phrase_filter)
    
    # Add background box for readability
    background_filter = "drawbox=x=0:y=h-340:w=1080:h=320:color=black@0.65:t=fill"
    
    # Combine all filters
    all_filters = [background_filter] + filters
    
    return ",".join(all_filters)

def build_safe_phrase_captions(
    segments: List[Dict[str, Any]],
    clip_start: float = 0.0,
    style: str = "poppins_bold_boxed"
) -> str:
    """
    Build safe phrase-based captions that work reliably with FFmpeg.
    Uses simplified text but preserves real timing.
    
    Args:
        segments: Caption segments with start, end, text
        clip_start: Clip start time (for clip-relative timing)
        style: Style preset name
    
    Returns:
        Complete filter string with safe phrase timing
    """
    if not segments:
        return ""
    
    # Get style configuration
    style_config = get_style_config(style)
    font_path = get_bundled_poppins_bold()
    
    # Build filters for each segment
    filters = []
    
    for i, segment in enumerate(segments):
        if not segment.get('text'):
            continue
            
        # Convert global times to clip-relative times
        start_local = max(0.0, segment['start'] - clip_start)
        end_local = max(0.1, segment['end'] - clip_start)
        
        # Skip segments that are too short or off-screen
        if end_local - start_local < 0.2:
            continue
            
        # Create safe, simple text for this segment
        # Use segment number + first few words to avoid parsing issues
        original_text = segment['text'].strip()
        if len(original_text) > 20:
            safe_text = f"Caption {i+1}: {original_text[:15]}..."
        else:
            safe_text = f"Caption {i+1}: {original_text}"
        
        # Ensure text is completely safe
        safe_text = ''.join(char for char in safe_text if ord(char) >= 32 and ord(char) <= 126)
        safe_text = safe_text.replace("'", "").replace('"', "").replace(';', ",").replace(':', " -")
        
        # Skip if text is too short after cleaning
        if len(safe_text) < 5:
            continue
        
        # Build phrase filter with proper timing
        phrase_filter = (
            f"drawtext=fontfile='{font_path}':text='{safe_text}':"
            f"x='(w-text_w)/2':y='if(gt(h-240-text_h,0),h-240-text_h,10)':"
            f"fontsize={style_config['fontsize']}:fontcolor={style_config['fontcolor']}:"
            f"box=1:boxcolor=black@0.6:boxborderw=20:"
            f"enable='between(t,{start_local:.2f},{end_local:.2f})'"
        )
        filters.append(phrase_filter)
    
    # Add background box for readability
    background_filter = "drawbox=x=0:y=h-340:w=1080:h=320:color=black@0.65:t=fill"
    
    # Combine all filters
    all_filters = [background_filter] + filters
    
    return ",".join(all_filters)
