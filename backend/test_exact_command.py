#!/usr/bin/env python3
"""
Test with the exact same FFmpeg command that the video processor is using.
"""

import subprocess
import os

def test_exact_command():
    """Test with the exact same FFmpeg command"""
    print("🔍 TESTING EXACT FFMPEG COMMAND FROM VIDEO PROCESSOR")
    print("=" * 50)
    
    # Find a test video
    outputs_dir = "outputs"
    clip_files = [f for f in os.listdir(outputs_dir) if f.endswith('.mp4')]
    
    if not clip_files:
        print("❌ No clip files found")
        return
    
    input_video = os.path.join(outputs_dir, clip_files[0])
    
    # Use the exact FFmpeg command from the video processor
    cmd = [
        "ffmpeg", "-i", input_video,
        "-vf", "drawtext=text='This room is like a red carpet Hollywood hallway.':enable='1':x='(w-text_w)/2':y='h-160':fontsize=48:fontcolor=white:fontfile='C:/Windows/Fonts/arial.ttf':box=1:boxcolor=black@0.6:boxborderw=20,drawtext=text='CAPS_OK':enable='1':x='(w-text_w)/2':y='h-240':fontsize=54:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=20",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "veryfast", "-crf", "23",
        "-r", "30", "-vsync", "cfr",
        "-profile:v", "baseline", "-level:v", "3.0", "-tag:v", "avc1",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart",
        "-y", os.path.join(outputs_dir, "test_exact_command.mp4")
    ]
    
    print(f"🔧 Testing exact command:")
    print(f"   {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(f"✅ Exact command worked!")
            
            output_video = os.path.join(outputs_dir, "test_exact_command.mp4")
            if os.path.exists(output_video):
                size = os.path.getsize(output_video)
                print(f"📁 Output: {output_video} ({size} bytes)")
                
                # Now extract a frame at t=1.0s to see if captions are visible
                frame_output = os.path.join(outputs_dir, "test_exact_command_frame.png")
                frame_cmd = [
                    "ffmpeg", "-ss", "1.0", "-i", output_video,
                    "-frames:v", "1", "-y", frame_output
                ]
                
                print(f"\n🔧 Extracting frame at t=1.0s...")
                frame_result = subprocess.run(frame_cmd, capture_output=True, text=True, timeout=30)
                
                if frame_result.returncode == 0:
                    if os.path.exists(frame_output):
                        frame_size = os.path.getsize(frame_output)
                        print(f"   ✅ Frame extracted: {frame_output} ({frame_size} bytes)")
                        print(f"   📸 Please visually check this frame for captions")
                        
                        # Clean up frame
                        os.remove(frame_output)
                    else:
                        print(f"   ❌ Frame file not created")
                else:
                    print(f"   ❌ Frame extraction failed: {frame_result.stderr[:200]}...")
                
                # Clean up output video
                os.remove(output_video)
            else:
                print(f"❌ Output file not created")
                
        else:
            print(f"❌ Exact command failed: {result.stderr[:200]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_exact_command()
