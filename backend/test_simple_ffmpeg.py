#!/usr/bin/env python3
"""
Simple test to test FFmpeg drawtext with the exact filter string that's failing.
"""

import subprocess
import os

def test_simple_ffmpeg():
    """Test a simple FFmpeg drawtext command"""
    print("🔍 TESTING SIMPLE FFMPEG DRAWTEXT")
    print("=" * 50)
    
    # Find a test video
    outputs_dir = "outputs"
    clip_files = [f for f in os.listdir(outputs_dir) if f.endswith('.mp4')]
    
    if not clip_files:
        print("❌ No clip files found")
        return
    
    input_video = os.path.join(outputs_dir, clip_files[0])
    output_video = os.path.join(outputs_dir, "test_simple_drawtext.mp4")
    
    print(f"📹 Input: {input_video}")
    print(f"📹 Output: {output_video}")
    
    # Test with a very simple filter string first
    simple_filter = "drawtext=text='TEST':x='(w-text_w)/2':y='h-160':fontsize=48:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=20"
    
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
            print("✅ Simple filter worked!")
            
            # Now test with a slightly more complex filter
            complex_filter = "drawtext=text='TEST':x='(w-text_w)/2':y='h-160':fontsize=48:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=20,drawtext=text='CAPS_OK':x='(w-text_w)/2':y='h-240':fontsize=54:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=20"
            
            print(f"\n🔧 Testing complex filter: {complex_filter}")
            
            output_video2 = os.path.join(outputs_dir, "test_complex_drawtext.mp4")
            cmd2 = [
                "ffmpeg", "-i", input_video,
                "-vf", complex_filter,
                "-t", "5",  # Limit to 5 seconds for testing
                "-y", output_video2
            ]
            
            print(f"🎬 Running: {' '.join(cmd2)}")
            
            result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=60)
            
            if result2.returncode == 0:
                print("✅ Complex filter worked!")
            else:
                print(f"❌ Complex filter failed: {result2.stderr}")
                
        else:
            print(f"❌ Simple filter failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Cleanup
    for output_file in [output_video, os.path.join(outputs_dir, "test_complex_drawtext.mp4")]:
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"🧹 Cleaned up: {output_file}")

if __name__ == "__main__":
    test_simple_ffmpeg()
