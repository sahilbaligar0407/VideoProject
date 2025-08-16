#!/usr/bin/env python3
"""
Test script for enhanced ClipGenius features.
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.highlight.snapping import (
    snap_to_transcript_boundary, 
    snap_to_audio_pause, 
    choose_clip_window, 
    duration_preference
)
from app.topic.search import topic_windows, keyword_spans
from app.video.vertical import get_vertical_dimensions, build_vertical_filter
from app.settings import settings


async def test_enhanced_features():
    """Test the new enhanced features"""
    print("🧪 Testing Enhanced ClipGenius Features")
    print("=" * 50)
    
    # Test 1: Duration preference function
    print("\n1️⃣ Testing duration preference function...")
    test_durations = [10, 20, 28, 35, 50, 70]
    for duration in test_durations:
        score = duration_preference(
            duration, 
            settings.target_clip_duration, 
            settings.min_clip_duration, 
            settings.max_clip_duration
        )
        print(f"   Duration {duration}s: score {score:.3f}")
    
    # Test 2: Clip window selection
    print("\n2️⃣ Testing clip window selection...")
    center_time = 120.0
    video_duration = 300.0
    duration_policy = {
        'min': settings.min_clip_duration,
        'target': settings.target_clip_duration,
        'max': settings.max_clip_duration
    }
    
    start, end = choose_clip_window(center_time, duration_policy, video_duration)
    print(f"   Center: {center_time}s, Video duration: {video_duration}s")
    print(f"   Selected window: {start:.1f}s - {end:.1f}s (duration: {end-start:.1f}s)")
    
    # Test 3: Vertical dimensions
    print("\n3️⃣ Testing vertical dimensions...")
    width, height = get_vertical_dimensions()
    print(f"   Vertical dimensions: {width}x{height} (9:16 aspect ratio)")
    
    # Test 4: Vertical filter building
    print("\n4️⃣ Testing vertical filter building...")
    test_cases = [
        (1920, 1080, "Landscape to vertical"),
        (1080, 1920, "Already vertical"),
        (1280, 720, "HD to vertical")
    ]
    
    for input_w, input_h, description in test_cases:
        filter_str = build_vertical_filter(input_w, input_h, 1080, 1920, bg_blur=True)
        print(f"   {description} ({input_w}x{input_h}): {filter_str[:50]}...")
    
    # Test 5: Topic search (keyword spans)
    print("\n5️⃣ Testing topic search...")
    test_segments = [
        {'start': 0, 'end': 10, 'text': 'This is about pricing and features.'},
        {'start': 10, 'end': 20, 'text': 'Let me explain the onboarding process.'},
        {'start': 20, 'end': 30, 'text': 'The pricing structure is very competitive.'},
        {'start': 30, 'end': 40, 'text': 'Onboarding takes about 2 weeks.'}
    ]
    
    query_words = ['pricing', 'onboarding']
    spans = keyword_spans(test_segments, query_words)
    print(f"   Found {len(spans)} spans for topics: {query_words}")
    for start, end, score in spans:
        print(f"     {start}s - {end}s (score: {score:.3f})")
    
    print("\n✅ All enhanced features tests completed successfully!")
    print("\n🎯 You can now use these features in ClipGenius:")
    print("   - Smart clip duration with clean endings")
    print("   - Topic-based clip search")
    print("   - Vertical 9:16 video output")
    print("   - Enhanced caption positioning")


if __name__ == "__main__":
    asyncio.run(test_enhanced_features())
