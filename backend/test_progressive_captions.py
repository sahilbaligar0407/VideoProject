#!/usr/bin/env python3
"""
Test script for the new progressive word-level caption system.
This tests the system without requiring existing ASS files.
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.captions.word_events import flatten_word_events
from app.captions.progressive import build_progressive_states
from app.captions.burn_drawtext import build_drawtext_filter

def test_progressive_caption_system():
    """Test the progressive caption system with sample data"""
    
    print("🧪 Testing Progressive Caption System")
    print("=" * 50)
    
    # Sample transcription segments (simulating Whisper output)
    sample_segments = [
        {
            "start": 0.0,
            "end": 2.5,
            "text": "This room is like a",
            "words": [
                {"word": "This", "start": 0.0, "end": 0.3},
                {"word": "room", "start": 0.4, "end": 0.8},
                {"word": "is", "start": 0.9, "end": 1.1},
                {"word": "like", "start": 1.2, "end": 1.6},
                {"word": "a", "start": 1.7, "end": 2.0}
            ]
        },
        {
            "start": 2.5,
            "end": 4.8,
            "text": "red carpet Hollywood hallway",
            "words": [
                {"word": "red", "start": 2.5, "end": 2.8},
                {"word": "carpet", "start": 2.9, "end": 3.4},
                {"word": "Hollywood", "start": 3.5, "end": 4.0},
                {"word": "hallway", "start": 4.1, "end": 4.8}
            ]
        },
        {
            "start": 5.0,
            "end": 7.2,
            "text": "I say we go to the movie exhibit next",
            "words": [
                {"word": "I", "start": 5.0, "end": 5.1},
                {"word": "say", "start": 5.2, "end": 5.5},
                {"word": "we", "start": 5.6, "end": 5.8},
                {"word": "go", "start": 5.9, "end": 6.1},
                {"word": "to", "start": 6.2, "end": 6.3},
                {"word": "the", "start": 6.4, "end": 6.5},
                {"word": "movie", "start": 6.6, "end": 6.9},
                {"word": "exhibit", "start": 7.0, "end": 7.2}
            ]
        },
        {
            "start": 7.5,
            "end": 9.8,
            "text": "Oh my gosh this is amazing",
            "words": [
                {"word": "Oh", "start": 7.5, "end": 7.7},
                {"word": "my", "start": 7.8, "end": 8.0},
                {"word": "gosh", "start": 8.1, "end": 8.4},
                {"word": "this", "start": 8.5, "end": 8.7},
                {"word": "is", "start": 8.8, "end": 9.0},
                {"word": "amazing", "start": 9.1, "end": 9.8}
            ]
        }
    ]
    
    print("📝 Sample segments:")
    for i, seg in enumerate(sample_segments):
        print(f"  {i+1}. {seg['text']} ({seg['start']:.1f}s - {seg['end']:.1f}s)")
        if 'words' in seg:
            print(f"     Words: {len(seg['words'])} words with timing")
    
    print("\n" + "=" * 50)
    
    # Test 1: Flatten word events
    print("🔍 Test 1: Flattening word events...")
    try:
        # Use clip timing for the test
        clip_start_abs = 0.0
        clip_end_abs = 10.0  # 10 second test clip
        word_events = flatten_word_events(sample_segments, clip_start_abs, clip_end_abs)
        print(f"✅ Flattened {len(word_events)} word events")
        
        print("   Word timeline:")
        for i, word in enumerate(word_events[:10]):  # Show first 10
            print(f"     {i+1}. '{word['text']}' at {word['start']:.2f}s")
        
        if len(word_events) > 10:
            print(f"     ... and {len(word_events) - 10} more words")
            
    except Exception as e:
        print(f"❌ Failed to flatten word events: {e}")
        return False
    
    print("\n" + "=" * 50)
    
    # Test 2: Build progressive states
    print("🔍 Test 2: Building progressive states...")
    try:
        states = build_progressive_states(
            word_events,
            max_words=5,
            lead_sec=0.18,
            min_dur_sec=0.12,
            overlap_sec=0.05
        )
        
        print(f"✅ Built {len(states)} progressive states")
        
        print("   Progressive caption states:")
        for i, state in enumerate(states):
            print(f"     {i+1}. '{state['text']}' ({state['start']:.2f}s - {state['end']:.2f}s)")
            print(f"        Words: {state['word_count']}")
        
    except Exception as e:
        print(f"❌ Failed to build progressive states: {e}")
        return False
    
    print("\n" + "=" * 50)
    
    # Test 3: Build drawtext filter
    print("🔍 Test 3: Building drawtext filter...")
    try:
        filter_string = build_drawtext_filter(
            clip_start=0.0,
            segments=sample_segments,
            style="poppins_bold_boxed",
            clip_id="test-clip-123"
        )
        
        if filter_string:
            print(f"✅ Generated filter string ({len(filter_string)} characters)")
            print(f"   Preview: {filter_string[:200]}...")
            
            # Check for key elements
            if "drawbox" in filter_string:
                print("   ✅ Contains background box")
            if "drawtext=" in filter_string:
                print("   ✅ Contains drawtext filters")
            if "Poppins" in filter_string:
                print("   ✅ Contains Poppins fonts")
                
        else:
            print("❌ Generated empty filter string")
            return False
            
    except Exception as e:
        print(f"❌ Failed to build drawtext filter: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Progressive caption system is working.")
    return True

if __name__ == "__main__":
    success = test_progressive_caption_system()
    if success:
        print("\n✅ Progressive caption system test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Progressive caption system test failed!")
        sys.exit(1)
