#!/usr/bin/env python3
"""
Test to check if the timing expression is working correctly.
"""

import subprocess
import os

def test_timing():
    """Test different timing expressions"""
    print("🔍 TESTING TIMING EXPRESSIONS")
    print("=" * 50)
    
    # Find a test video
    outputs_dir = "outputs"
    clip_files = [f for f in os.listdir(outputs_dir) if f.endswith('.mp4')]
    
    if not clip_files:
        print("❌ No clip files found")
        return
    
    input_video = os.path.join(outputs_dir, clip_files[0])
    
    # Test different timing expressions
    timing_tests = [
        ("Always visible", "1"),
        ("First 3 seconds", "between(t,0,3)"),
        ("After 1 second", "gt(t,1)"),
        ("Between 2-5 seconds", "between(t,2,5)")
    ]
    
    for test_name, timing_expr in timing_tests:
        print(f"\n🔧 Testing: {test_name}")
        print(f"   Timing: {timing_expr}")
        
        output_video = os.path.join(outputs_dir, f"test_timing_{test_name.replace(' ', '_').lower()}.mp4")
        
        # Create filter string
        filter_string = f"drawtext=text='{test_name}':enable='{timing_expr}':x='(w-text_w)/2':y='h-160':fontsize=48:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=20"
        
        print(f"   Filter: {filter_string}")
        
        cmd = [
            "ffmpeg", "-i", input_video,
            "-vf", filter_string,
            "-t", "10",  # Limit to 10 seconds for testing
            "-y", output_video
        ]
        
        print(f"   Running FFmpeg...")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"   ✅ {test_name} worked!")
                
                # Check if output file was created and has reasonable size
                if os.path.exists(output_video):
                    size = os.path.getsize(output_video)
                    print(f"   📁 Output: {output_video} ({size} bytes)")
                    
                    # Clean up
                    os.remove(output_video)
                else:
                    print(f"   ❌ Output file not created")
                    
            else:
                print(f"   ❌ {test_name} failed: {result.stderr[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_timing()
