#!/usr/bin/env python3
"""
Test the improved MoviePy caption system with better visibility settings.
"""

import os
import json
import sys

# Add the app directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from captions.moviepy_captions import process_video_with_captions

def test_improved_captions():
    """Test the improved caption system with better visibility."""
    
    clip_id = "clip_1_6613faa6-b6ce-410d-885b-0f0ba58390c3"
    video_path = f"outputs/{clip_id}.mp4"
    json_path = f"outputs/{clip_id}.json"
    
    print(f"🧪 Testing IMPROVED MoviePy caption system for: {clip_id}")
    print("=" * 70)
    
    # Check if files exist
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        return False
    
    # Load transcription data
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            clip_data = json.load(f)
        
        segments = clip_data.get('segments', [])
        print(f"✅ Loaded {len(segments)} transcription segments")
        
        # Convert segments to word-level data for MoviePy
        word_data = []
        for segment in segments:
            word_data.append({
                'word': segment['text'],
                'start': float(segment['start']),
                'end': float(segment['end'])
            })
        
        print(f"🔍 Converted to {len(word_data)} word-level entries")
        
        # Debug: show first few entries
        for i, entry in enumerate(word_data[:3]):
            print(f"   Entry {i+1}: '{entry['word']}' ({entry['start']:.2f}s - {entry['end']:.2f}s)")
        
        # Test with IMPROVED settings (should use new defaults)
        test_output = f"outputs/{clip_id}_improved_test.mp4"
        
        print(f"🎯 Testing with IMPROVED caption settings:")
        print(f"   📍 Position: bottom80 (instead of bottom75)")
        print(f"   🎨 Font size: 8.0 (instead of 4.0)")
        print(f"   🌈 Background: 60% opacity black (instead of transparent)")
        print(f"   📝 Max chars: 25 (instead of 10)")
        
        result = process_video_with_captions(
            video_path=video_path,
            transcription_data=word_data,
            clip_id=clip_id
            # Should use new defaults: fontsize=8.0, background_opacity=0.6, position=bottom80
        )
        
        if result and os.path.exists(result):
            print(f"✅ IMPROVED captioned video created: {result}")
            print(f"📊 Size: {os.path.getsize(result)} bytes")
            
            # Rename to test version
            if os.path.exists(test_output):
                os.remove(test_output)
            os.rename(result, test_output)
            print(f"🔄 Renamed to: {test_output}")
            
            print(f"\n🎯 Now check if '{test_output}' has visible captions!")
            print(f"   - Should show white text with black background")
            print(f"   - Should be much larger and more visible than before")
            print(f"   - Should be positioned at 80% from top of screen")
            
            return True
        else:
            print(f"❌ Failed to create improved captioned video")
            return False
            
    except Exception as e:
        print(f"❌ Error in improved caption test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_improved_captions()
    
    if success:
        print("\n🎉 SUCCESS! Improved caption system is working!")
        print("📝 Check the generated video for much more visible captions.")
    else:
        print("\n💥 FAILED! There's still an issue with the improved caption system.")
    
    print("\n" + "=" * 70)
