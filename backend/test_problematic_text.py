#!/usr/bin/env python3
"""
Test FFmpeg drawtext with the exact problematic text that's causing issues.
"""

import subprocess
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.captions.burn_drawtext import build_single_drawtext

def test_problematic_text():
    """Test FFmpeg drawtext with problematic text"""
    print("🔍 TESTING PROBLEMATIC TEXT IN DRAWTEXT")
    print("=" * 50)
    
    # Find a test video
    outputs_dir = "outputs"
    clip_files = [f for f in os.listdir(outputs_dir) if f.endswith('.mp4')]
    
    if not clip_files:
        print("❌ No clip files found")
        return
    
    input_video = os.path.join(outputs_dir, clip_files[0])
    output_video = os.path.join(outputs_dir, "test_problematic_text.mp4")
    
    print(f"📹 Input: {input_video}")
    print(f"📹 Output: {output_video}")
    
    # Test with the exact problematic text from our filter
    problematic_texts = [
        "There's so many creators make full-on movies;",
        "I feel like we just walked onto a movie set.",
        "This is a Roblox music video and there's so many bacon hairs in this video; it's crazy."
    ]
    
    for i, text in enumerate(problematic_texts):
        print(f"\n🔧 Testing text {i+1}: {text}")
        
        # Use the new build_single_drawtext function
        filter_string = build_single_drawtext(
            text=text,
            start_time=0.0,
            end_time=3.0,
            fontfile='C:/Windows/Fonts/arial.ttf'
        )
        
        print(f"   Generated filter: {filter_string}")
        
        # Test with FFmpeg
        cmd = [
            "ffmpeg", "-i", input_video,
            "-vf", filter_string,
            "-t", "3",  # Limit to 3 seconds for testing
            "-y", output_video
        ]
        
        print(f"   Running FFmpeg...")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"   ✅ Text {i+1} worked!")
            else:
                print(f"   ❌ Text {i+1} failed: {result.stderr[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Cleanup
    if os.path.exists(output_video):
        os.remove(output_video)
        print(f"\n🧹 Cleaned up: {output_video}")

if __name__ == "__main__":
    test_problematic_text()
