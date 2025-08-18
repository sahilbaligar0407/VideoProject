#!/usr/bin/env python3
"""
Simple test to verify MoviePy captions are working with basic settings.
"""

import os
import sys

# Add the app directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from captions.moviepy_captions import process_video_with_captions

def test_simple_captions():
    """Test with very simple, visible caption settings."""
    
    clip_id = "clip_1_70dbf0b1-e93f-4c66-9998-412afe0b79ca"
    video_path = f"outputs/{clip_id}.mp4"
    
    print(f"🧪 Testing simple caption generation for: {clip_id}")
    print("=" * 60)
    
    # Create very simple test data - just one caption that should be visible
    test_data = [
        {
            'word': 'TEST CAPTION - SHOULD BE VISIBLE',
            'start': 1.0,  # Start at 1 second
            'end': 5.0      # Show for 4 seconds
        }
    ]
    
    print(f"📝 Test caption: '{test_data[0]['word']}'")
    print(f"⏰ Timing: {test_data[0]['start']}s - {test_data[0]['end']}s")
    
    # Test with maximum visibility settings
    test_output = f"outputs/{clip_id}_simple_test.mp4"
    
    try:
        result = process_video_with_captions(
            video_path=video_path,
            transcription_data=test_data,
            clip_id=clip_id,
            fontsize=15.0,  # 15% of frame height = very large
            max_chars=100,  # Allow long text
            color="red",    # Bright red color
            highlight_color="yellow",
            background_opacity=0.8,  # Very visible background
            position="center"  # Dead center of screen
        )
        
        if result and os.path.exists(result):
            print(f"✅ Simple test captioned video created: {result}")
            print(f"📊 Size: {os.path.getsize(result)} bytes")
            
            # Rename to test version
            if os.path.exists(test_output):
                os.remove(test_output)
            os.rename(result, test_output)
            print(f"🔄 Renamed to: {test_output}")
            
            print(f"\n🎯 Now check if '{test_output}' has a visible red caption!")
            print(f"   - Should show 'TEST CAPTION - SHOULD BE VISIBLE'")
            print(f"   - Should be bright red text with black background")
            print(f"   - Should appear at 1-5 seconds in the center of the video")
            
            return True
        else:
            print(f"❌ Failed to create simple test captioned video")
            return False
            
    except Exception as e:
        print(f"❌ Error in simple caption test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_captions()
    
    if success:
        print("\n🎉 SUCCESS! Simple test completed.")
        print("📝 Check the generated video for visible captions.")
    else:
        print("\n💥 FAILED! There's a fundamental issue with the caption system.")
    
    print("\n" + "=" * 60)
