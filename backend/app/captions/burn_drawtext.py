#!/usr/bin/env python3
"""
Bulletproof drawtext filter builder for FFmpeg caption burning.
Supports Poppins fonts, progressive word building, and viral word highlighting.
Implements the "Builder" flow with proper escaping and width fitting.
"""

import random
import re
import os
from typing import List, Dict, Any

# Wow/Hook words that get highlighted with Poppins-ExtraBold
WOW = set(map(str.lower, [
    "wow", "omg", "holy", "insane", "unbelievable", "incredible", "amazing", 
    "massive", "huge", "shocking", "viral", "trending", "must", "secret", 
    "hack", "crazy"
]))

def ff_esc(s: str) -> str:
    """
    Strict escaping for ffmpeg drawtext.
    Order matters: backslash first, then other problematic characters.
    """
    if s is None:
        return ""
    
    # Order matters: backslash first
    s = s.replace("\\", "\\\\")
    # Escape single quote (we use single-quoted text)
    s = s.replace("'", r"\'")
    # Also guard punctuation that can leak out of arg parsing in some builds
    for ch in [":", ",", ";", "[", "]", "%", "="]:
        s = s.replace(ch, "\\" + ch)
    # Newlines to \n
    s = s.replace("\r\n", r"\n").replace("\n", r"\n")
    
    return s

def _font_arg(path: str) -> str:
    """Format font path argument with proper escaping"""
    # Keep single quotes and escape colon/backslashes inside
    p = path.replace("\\", "\\\\").replace(":", "\\:")
    return f"fontfile='{p}'"

def build_drawtext_from_states(
    states: List[Dict[str, Any]],
    font_black: str,
    font_extrabold: str,
    font_bold: str,
    fontsize: int,
    margin_bottom: int,
    clip_seed: int
) -> str:
    """
    Returns a single -vf string:
      format=yuv420p,drawbox=..., [many drawtext=... enable='between(t,...)']
    
    We render each state as a single line, but with spans using separate drawtext calls
    to mix fonts. One random Bold per window (not a WOW) and WOW->ExtraBold.
    
    Args:
        states: List of progressive caption states
        font_black: Path to Poppins-Black.ttf
        font_extrabold: Path to Poppins-ExtraBold.ttf
        font_bold: Path to Poppins-Bold.ttf
        fontsize: Base font size
        margin_bottom: Bottom margin for text positioning
        clip_seed: Seed for reproducible random bold word selection
        
    Returns:
        Complete FFmpeg filter string
    """
    rng = random.Random(clip_seed)

    # Background and format
    prefix = "format=yuv420p,drawbox=x=0:y=h-340:w=iw:h=320:color=black@0.65:t=fill"
    parts = [prefix]

    # Font arguments
    fb = _font_arg(font_black)      # Default font
    fe = _font_arg(font_extrabold)  # Wow/hook words
    fbo = _font_arg(font_bold)      # Random bold words

    for st in states:
        toks = st["tokens"]
        if not toks:
            continue

        # Choose one random bold index among non-WOW tokens
        candidate_idx = [i for i, t in enumerate(toks) if t.lower() not in WOW]
        bold_idx = rng.choice(candidate_idx) if candidate_idx else None

        # Build spans: [(text, fontarg)]
        spans = []
        for i, tok in enumerate(toks):
            tclean = tok  # Already cleaned upstream
            font = fe if tclean.lower() in WOW else (fbo if bold_idx == i else fb)
            spans.append((tclean, font))

        # Shared geometry & timing
        enable = f"enable='between(t,{st['start']:.3f},{st['end']:.3f})'"
        geom = "x=(w-text_w)/2:y=h-260"
        common = f"{enable}:{geom}:fontsize={int(fontsize)}:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=20"

        # One centering pass (invisible) to stabilize text_w across spans
        # Use an empty space with base font; it still allocates width.
        parts.append(f"drawtext={fb}:text=' ':{common}")

        # Now actual visible spans layered in order; each uses its own fontfile and text
        text_so_far = []
        for text, fontarg in spans:
            text_so_far.append(text)
            visible = ff_esc(" ".join(text_so_far))
            parts.append(f"drawtext={fontarg}:text='{visible}':{common}")

    return ",".join(parts)

def validate_filter_string(vf: str) -> bool:
    """Simple sanity checks for the filter string"""
    # Check for basic structure
    if not vf:
        return False
    
    # Should contain drawtext filters
    if "drawtext=" not in vf:
        return False
    
    # Should contain enable expressions
    if "enable='between(t," not in vf:
        return False
    
    # Should contain background elements
    if "drawbox" not in vf:
        return False
    
    return True

def build_drawtext_filter(
    clip_start: float,
    segments: List[Dict[str, Any]],
    style: str = "poppins_bold_boxed",
    debug_watermark: bool = False,
    clip_id: str = None
) -> str:
    """
    Build complete drawtext filter for caption burning.
    
    Args:
        clip_start: Clip start time (for clip-relative timing)
        segments: Caption segments with start, end, text
        style: Style preset name
        debug_watermark: Whether to add debug watermark (deprecated, handled by video processor)
        clip_id: Clip ID for seeding random number generator
        
    Returns:
        Complete drawtext filter string with progressive word-level timing
    """
    if not segments:
        return ""
    
    # Import the new progressive caption system
    from .word_events import flatten_word_events
    from .progressive import build_progressive_states
    
    # Get settings for caption configuration
    from app.settings import settings
    max_words = getattr(settings, "max_words_per_caption", 5)
    lead_sec = getattr(settings, "caption_lead_sec", 0.18)
    min_dur = getattr(settings, "min_caption_dur", 0.12)
    overlap_sec = getattr(settings, "caption_overlap_sec", 0.05)
    
    # Calculate clip end time (approximate if not available)
    clip_end = clip_start + 60.0  # Default 60s clip, adjust as needed
    
    # 1) Flatten segments into word events (keeps ALL speakers)
    all_words = flatten_word_events(
        segments, 
        clip_start, 
        clip_end, 
        pad_head=0.25, 
        pad_tail=0.25
    )
    
    # 2) Build progressive states that build up to max_words then clear
    states = build_progressive_states(
        all_words,
        max_words=max_words,
        lead_sec=lead_sec,
        min_dur_sec=min_dur,
        overlap_sec=overlap_sec
    )
    
    # 3) Get Poppins fonts from outputs/ directory
    root = os.path.abspath("outputs")
    font_black = os.path.join(root, "Poppins-Black.ttf")
    font_bold = os.path.join(root, "Poppins-Bold.ttf")
    font_extra = os.path.join(root, "Poppins-ExtraBold.ttf")
    
    # Check if fonts exist
    missing = [p for p in [font_black, font_bold, font_extra] if not os.path.exists(p)]
    if missing:
        raise Exception(f"Poppins fonts not found in outputs/: {missing}")
    
    print(f"✅ Using Poppins Black font: {font_black}")
    print(f"✅ Using Poppins Bold font: {font_bold}")
    print(f"✅ Using Poppins ExtraBold font: {font_extra}")
    
    # 4) Create seeded random number generator for reproducible bold word selection
    clip_seed = hash(clip_id) & 0xFFFFFFFF if clip_id else 0
    
    # 5) Build drawtext filter from progressive states
    main_filter = build_drawtext_from_states(
        states,
        font_black=font_black,
        font_extrabold=font_extra,
        font_bold=font_bold,
        fontsize=54,  # Default size
        margin_bottom=260,  # Safe bottom margin
        clip_seed=clip_seed
    )
    
    print(f"🔍 Generated progressive word-level filter with {len(states)} caption states")
    print(f"🔍 Using Poppins Black for base text, Bold for random words, ExtraBold for viral words")
    
    return main_filter
