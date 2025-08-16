#!/usr/bin/env python3
"""
Test with the exact text that's failing to see if there's an issue with the text content.
"""

import subprocess
import os

def test_exact_text():
    """Test with the exact text that's failing"""
    print("🔍 TESTING EXACT TEXT THAT'S FAILING")
    print("=" * 50)
    
    # Find a test video
    outputs_dir = "outputs"
    clip_files = [f for f in os.listdir(outputs_dir) if f.endswith('.mp4')]
    
    if not clip_files:
        print("❌ No clip files found")
        return
    
    input_video = os.path.join(outputs_dir, clip_files[0])
    
    # Test with the exact text that's failing
    exact_text = "This room is like a red carpet Hollywood hallway."
    
    print(f"📝 Testing text: {exact_text}")
    print(f"📏 Text length: {len(exact_text)} characters")
    
    output_video = os.path.join(outputs_dir, "test_exact_text.mp4")
    
    # Create filter string with the exact text
    filter_string = f"drawtext=text='{exact_text}':enable='1':x='(w-text_w)/2':y='h-160':fontsize=48:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=20"
    
    print(f"🔧 Filter: {filter_string}")
    
    cmd = [
        "ffmpeg", "-i", input_video,
        "-vf", filter_string,
        "-t", "5",  # Limit to 5 seconds for testing
        "-y", output_video
    ]
    
    print(f"🎬 Running FFmpeg...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ Exact text worked!")
            
            # Check if output file was created and has reasonable size
            if os.path.exists(output_video):
                size = os.path.getsize(output_video)
                print(f"📁 Output: {output_video} ({size} bytes)")
                
                # Test with a shorter text to compare
                short_text = "TEST"
                short_filter = f"drawtext=text='{short_text}':enable='1':x='(w-text_w)/2':y='h-160':fontsize=48:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=20"
                
                print(f"\n🔧 Testing short text: {short_text}")
                print(f"   Filter: {short_filter}")
                
                short_output = os.path.join(outputs_dir, "test_short_text.mp4")
                short_cmd = [
                    "ffmpeg", "-i", input_video,
                    "-vf", short_filter,
                    "-t", "5",
                    "-y", short_output
                ]
                
                short_result = subprocess.run(short_cmd, capture_output=True, text=True, timeout=60)
                
                if short_result.returncode == 0:
                    short_size = os.path.getsize(short_output)
                    print(f"   ✅ Short text worked! Size: {short_size} bytes")
                    print(f"   📊 Size difference: {size} vs {short_size} bytes")
                    
                    # Clean up short text file
                    os.remove(short_output)
                else:
                    print(f"   ❌ Short text failed: {short_result.stderr[:200]}...")
                
                # Clean up exact text file
                os.remove(output_video)
            else:
                print(f"❌ Output file not created")
                
        else:
            print(f"❌ Exact text failed: {result.stderr[:200]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_exact_text()
