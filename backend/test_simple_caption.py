#!/usr/bin/env python3
"""
Simple test with just one caption to test basic functionality.
"""

import subprocess
import os

def test_simple_caption():
    """Test with just one simple caption"""
    print("🔍 TESTING SIMPLE CAPTION")
    print("=" * 50)
    
    # Find a test video
    outputs_dir = "outputs"
    clip_files = [f for f in os.listdir(outputs_dir) if f.endswith('.mp4')]
    
    if not clip_files:
        print("❌ No clip files found")
        return
    
    input_video = os.path.join(outputs_dir, clip_files[0])
    output_video = os.path.join(outputs_dir, "test_simple_caption.mp4")
    
    print(f"📹 Input: {input_video}")
    print(f"📹 Output: {output_video}")
    
    # Test with a very simple filter string - just one caption
    simple_filter = "drawtext=text='TEST CAPTION':x='(w-text_w)/2':y='h-160':fontsize=48:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=20"
    
    print(f"\n🔧 Testing simple filter: {simple_filter}")
    
    cmd = [
        "ffmpeg", "-i", input_video,
        "-vf", simple_filter,
        "-t", "5",  # Limit to 5 seconds for testing
        "-y", output_video
    ]
    
    print(f"🎬 Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Simple caption worked!")
            
            # Now test with a slightly more complex filter - two captions
            complex_filter = "drawtext=text='FIRST':x='(w-text_w)/2':y='h-160':fontsize=48:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=20,drawtext=text='SECOND':x='(w-text_w)/2':y='h-200':fontsize=48:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=20"
            
            print(f"\n🔧 Testing complex filter: {complex_filter}")
            
            output_video2 = os.path.join(outputs_dir, "test_complex_caption.mp4")
            cmd2 = [
                "ffmpeg", "-i", input_video,
                "-vf", complex_filter,
                "-t", "5",  # Limit to 5 seconds for testing
                "-y", output_video2
            ]
            
            print(f"🎬 Running: {' '.join(cmd2)}")
            
            result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=60)
            
            if result2.returncode == 0:
                print("✅ Complex caption worked!")
            else:
                print(f"❌ Complex caption failed: {result2.stderr}")
                
        else:
            print(f"❌ Simple caption failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Cleanup
    for output_file in [output_video, os.path.join(outputs_dir, "test_complex_caption.mp4")]:
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"🧹 Cleaned up: {output_file}")

if __name__ == "__main__":
    test_simple_caption()
