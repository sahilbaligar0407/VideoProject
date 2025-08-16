#!/usr/bin/env python3
"""
Simple test of drawtext filter to isolate the issue.
"""

import subprocess
import os

def test_simple_drawtext():
    """Test a simple drawtext filter"""
    print("🧪 TESTING SIMPLE DRAWTEXT")
    print("=" * 40)
    
    # Create a simple test video
    test_video = "test_simple.mp4"
    cmd = [
        "ffmpeg", "-f", "lavfi", 
        "-i", "color=c=blue:size=1080x1920:duration=3",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", 
        "-preset", "ultrafast", "-y", test_video
    ]
    
    print(f"🎬 Creating test video...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to create test video: {result.stderr}")
        return
    
    print(f"✅ Test video created: {test_video}")
    
    # Test with a very simple drawtext filter
    output_video = "test_simple_captioned.mp4"
    
    # Simple filter: just one drawtext with basic text
    simple_filter = "drawtext=text='Hello World':x='(w-text_w)/2':y='h-100':fontsize=48:fontcolor=white"
    
    cmd = [
        "ffmpeg", "-i", test_video,
        "-vf", simple_filter,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "ultrafast", "-y", output_video
    ]
    
    print(f"\n🔥 Testing simple drawtext filter...")
    print(f"🔍 Filter: {simple_filter}")
    print(f"🔧 Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Simple drawtext succeeded!")
        
        if os.path.exists(output_video):
            size = os.path.getsize(output_video)
            print(f"📁 Output: {output_video} ({size} bytes)")
            
            # Extract frame to verify
            frame_path = "test_simple_frame.png"
            cmd = [
                "ffmpeg", "-ss", "1.0", "-i", output_video,
                "-frames:v", "1", "-y", frame_path
            ]
            subprocess.run(cmd, capture_output=True)
            
            if os.path.exists(frame_path):
                frame_size = os.path.getsize(frame_path)
                print(f"📸 Frame: {frame_path} ({frame_size} bytes)")
                os.remove(frame_path)
        else:
            print(f"❌ Output file not found")
    else:
        print(f"❌ Simple drawtext failed: {result.stderr}")
    
    # Cleanup
    print(f"\n🧹 Cleaning up...")
    for file in [test_video, output_video]:
        if os.path.exists(file):
            os.remove(file)
            print(f"   Removed: {file}")
    
    print(f"\n✅ Simple drawtext test complete!")

if __name__ == "__main__":
    test_simple_drawtext()
