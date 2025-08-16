#!/usr/bin/env python3
"""
Test with the exact filter string from our code to see if it works directly with FFmpeg.
"""

import subprocess
import os

def test_exact_filter():
    """Test with the exact filter string from our code"""
    print("🔍 TESTING EXACT FILTER FROM OUR CODE")
    print("=" * 50)
    
    # Find a test video
    outputs_dir = "outputs"
    clip_files = [f for f in os.listdir(outputs_dir) if f.endswith('.mp4')]
    
    if not clip_files:
        print("❌ No clip files found")
        return
    
    input_video = os.path.join(outputs_dir, clip_files[0])
    
    # Use the exact filter string from our code
    exact_filter = "drawtext=text='This room is like a red carpet Hollywood hallway.':enable='1':x='(w-text_w)/2':y='h-160':fontsize=48:fontcolor=white:fontfile='C:/Windows/Fonts/arial.ttf':box=1:boxcolor=black@0.6:boxborderw=20"
    
    print(f"🔧 Testing exact filter: {exact_filter}")
    
    output_video = os.path.join(outputs_dir, "test_exact_filter.mp4")
    
    cmd = [
        "ffmpeg", "-i", input_video,
        "-vf", exact_filter,
        "-t", "10",  # Limit to 10 seconds for testing
        "-y", output_video
    ]
    
    print(f"🎬 Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ Exact filter worked!")
            
            # Check if output file was created and has reasonable size
            if os.path.exists(output_video):
                size = os.path.getsize(output_video)
                print(f"📁 Output: {output_video} ({size} bytes)")
                
                # Now test with the CAPS_OK watermark added
                watermark_filter = exact_filter + ",drawtext=text='CAPS_OK':enable='1':x='(w-text_w)/2':y='h-240':fontsize=54:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=20"
                
                print(f"\n🔧 Testing with CAPS_OK watermark:")
                print(f"   Filter: {watermark_filter}")
                
                watermark_output = os.path.join(outputs_dir, "test_exact_filter_with_watermark.mp4")
                watermark_cmd = [
                    "ffmpeg", "-i", input_video,
                    "-vf", watermark_filter,
                    "-t", "10",
                    "-y", watermark_output
                ]
                
                watermark_result = subprocess.run(watermark_cmd, capture_output=True, text=True, timeout=60)
                
                if watermark_result.returncode == 0:
                    watermark_size = os.path.getsize(watermark_output)
                    print(f"   ✅ With watermark worked! Size: {watermark_size} bytes")
                    print(f"   📊 Size difference: {size} vs {watermark_size} bytes")
                    
                    # Clean up watermark file
                    os.remove(watermark_output)
                else:
                    print(f"   ❌ With watermark failed: {watermark_result.stderr[:200]}...")
                
                # Clean up exact filter file
                os.remove(output_video)
            else:
                print(f"❌ Output file not created")
                
        else:
            print(f"❌ Exact filter failed: {result.stderr[:200]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_exact_filter()
