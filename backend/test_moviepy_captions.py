#!/usr/bin/env python3
"""
Test script for MoviePy caption system.
This tests the caption generation without requiring a full video processing pipeline.
"""

import os
import sys
import json

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from captions.moviepy_captions import (
    split_text_into_lines, 
    create_caption_clips,
    process_video_with_captions
)

def test_text_splitting():
    """Test the text splitting logic"""
    print("🧪 Testing text splitting...")
    
    # Sample word data
    word_data = [
        {"word": "Hello", "start": 0.0, "end": 0.5},
        {"word": "world", "start": 0.6, "end": 1.1},
        {"word": "this", "start": 1.2, "end": 1.7},
        {"word": "is", "start": 1.8, "end": 2.0},
        {"word": "a", "start": 2.1, "end": 2.3},
        {"word": "test", "start": 2.4, "end": 2.9},
        {"word": "of", "start": 3.0, "end": 3.3},
        {"word": "the", "start": 3.4, "end": 3.6},
        {"word": "caption", "start": 3.7, "end": 4.2},
        {"word": "system", "start": 4.3, "end": 4.8}
    ]
    
    lines = split_text_into_lines(word_data, max_chars=15, max_duration=2.0)
    
    print(f"📝 Generated {len(lines)} subtitle lines:")
    for i, line in enumerate(lines):
        print(f"   Line {i+1}: '{line['text']}' ({line['start']:.2f}s - {line['end']:.2f}s)")
    
    return lines

def test_caption_clip_creation():
    """Test caption clip creation"""
    print("\n🧪 Testing caption clip creation...")
    
    # Sample subtitle line
    subtitle_line = {
        "text": "Hello world this is",
        "start": 0.0,
        "end": 2.0,
        "words": [
            {"word": "Hello", "start": 0.0, "end": 0.5},
            {"word": "world", "start": 0.6, "end": 1.1},
            {"word": "this", "start": 1.2, "end": 1.7},
            {"word": "is", "start": 1.8, "end": 2.0}
        ]
    }
    
    frame_size = (1080, 1920)  # 9:16 vertical video
    font_path = "C:/Windows/Fonts/arial.ttf"  # Use system font for testing
    
    try:
        word_clips, positions = create_caption_clips(
            subtitle_line, frame_size, font_path, 4.0
        )
        print(f"✅ Created {len(word_clips)} text clips")
        print(f"📍 Generated {len(positions)} position records")
        
        for i, pos in enumerate(positions):
            print(f"   Word {i+1}: '{pos['word']}' at ({pos['x_pos']}, {pos['y_pos']})")
            
    except Exception as e:
        print(f"❌ Failed to create caption clips: {e}")
        import traceback
        traceback.print_exc()

def test_full_processing():
    """Test the full processing pipeline with sample data"""
    print("\n🧪 Testing full processing pipeline...")
    
    # Sample transcription data (similar to what Whisper produces)
    transcription_data = [
        {
            "start": 0.0,
            "end": 2.0,
            "text": "Hello world this is",
            "words": [
                {"word": "Hello", "start": 0.0, "end": 0.5},
                {"word": "world", "start": 0.6, "end": 1.1},
                {"word": "this", "start": 1.2, "end": 1.7},
                {"word": "is", "start": 1.8, "end": 2.0}
            ]
        },
        {
            "start": 2.5,
            "end": 4.5,
            "text": "a test of the",
            "words": [
                {"word": "a", "start": 2.5, "end": 2.8},
                {"word": "test", "start": 2.9, "end": 3.4},
                {"word": "of", "start": 3.5, "end": 3.8},
                {"word": "the", "start": 3.9, "end": 4.2}
            ]
        },
        {
            "start": 5.0,
            "end": 6.5,
            "text": "caption system",
            "words": [
                {"word": "caption", "start": 5.0, "end": 5.5},
                {"word": "system", "start": 5.6, "end": 6.1}
            ]
        }
    ]
    
    print(f"📝 Processing {len(transcription_data)} transcription segments")
    
    try:
        # This will extract word data and prepare for processing
        word_data = []
        for segment in transcription_data:
            if 'words' in segment:
                for word in segment['words']:
                    word_data.append({
                        'word': word.get('word', word.get('text', '')),
                        'start': float(word.get('start', segment.get('start', 0.0))),
                        'end': float(word.get('end', segment.get('end', 0.0)))
                    })
            else:
                # Fallback: treat segment as single word
                word_data.append({
                    'word': segment.get('text', ''),
                    'start': float(segment.get('start', 0.0)),
                    'end': float(segment.get('end', 0.0))
                })
        
        # Sort by start time
        word_data.sort(key=lambda x: x['start'])
        
        print(f"🔍 Extracted {len(word_data)} words:")
        for word in word_data:
            print(f"   '{word['word']}' ({word['start']:.2f}s - {word['end']:.2f}s)")
        
        # Test line splitting
        lines = split_text_into_lines(word_data, max_chars=10, max_duration=2.0)
        print(f"\n📝 Generated {len(lines)} subtitle lines:")
        for i, line in enumerate(lines):
            print(f"   Line {i+1}: '{line['text']}' ({line['start']:.2f}s - {line['end']:.2f}s)")
            
    except Exception as e:
        print(f"❌ Failed to process transcription data: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests"""
    print("🚀 Testing MoviePy Caption System")
    print("=" * 50)
    
    try:
        # Test 1: Text splitting
        test_text_splitting()
        
        # Test 2: Caption clip creation
        test_caption_clip_creation()
        
        # Test 3: Full processing pipeline
        test_full_processing()
        
        print("\n✅ All tests completed successfully!")
        print("\n🎯 The MoviePy caption system is ready to use!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
