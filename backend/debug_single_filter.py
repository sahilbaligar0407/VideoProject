#!/usr/bin/env python3
"""
Debug script to test single drawtext filter construction.
"""

import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.captions.burn_drawtext import build_single_drawtext, escape_text_for_drawtext

def debug_single_filter():
    """Debug a single drawtext filter construction"""
    print("🔍 DEBUGGING SINGLE DRAWTEXT FILTER")
    print("=" * 50)
    
    # Test with a simple caption
    text = "This is a test caption"
    start_time = 0.0
    end_time = 5.0
    
    print(f"📝 Text: {text}")
    print(f"⏰ Timing: {start_time}s -> {end_time}s")
    
    # Test text escaping
    print(f"\n🔧 Text escaping:")
    escaped_text = escape_text_for_drawtext(text)
    print(f"   Original: {text}")
    print(f"   Escaped: {escaped_text}")
    
    # Test single filter construction
    print(f"\n🔧 Single filter construction:")
    single_filter = build_single_drawtext(
        text=text,
        start_time=start_time,
        end_time=end_time,
        fontfile='C:/Windows/Fonts/arial.ttf'
    )
    
    print(f"   Filter: {single_filter}")
    print(f"   Length: {len(single_filter)}")
    
    # Test multiple filters
    print(f"\n🔧 Multiple filters:")
    filter1 = build_single_drawtext(
        text="First caption",
        start_time=0.0,
        end_time=3.0,
        fontfile='C:/Windows/Fonts/arial.ttf'
    )
    
    filter2 = build_single_drawtext(
        text="Second caption",
        start_time=3.0,
        end_time=6.0,
        fontfile='C:/Windows/Fonts/arial.ttf'
    )
    
    combined = f"{filter1},{filter2}"
    print(f"   Filter 1: {filter1}")
    print(f"   Filter 2: {filter2}")
    print(f"   Combined: {combined}")
    
    # Test splitting
    print(f"\n🔧 Testing split:")
    parts = combined.split(",")
    print(f"   Split parts: {len(parts)}")
    for i, part in enumerate(parts):
        print(f"   Part {i+1}: {part[:100]}...")
    
    # Test with problematic text
    print(f"\n🔧 Problematic text test:")
    problematic_text = "This has 'quotes' and \"double quotes\" and, commas"
    escaped_problematic = escape_text_for_drawtext(problematic_text)
    print(f"   Original: {problematic_text}")
    print(f"   Escaped: {escaped_problematic}")
    
    problematic_filter = build_single_drawtext(
        text=problematic_text,
        start_time=0.0,
        end_time=3.0,
        fontfile='C:/Windows/Fonts/arial.ttf'
    )
    print(f"   Filter: {problematic_filter}")

if __name__ == "__main__":
    debug_single_filter()
