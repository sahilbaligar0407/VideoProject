#!/usr/bin/env python3
"""
Test clean ASS generation and caption burning.
"""

import os
import sys
import asyncio
import subprocess

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.captions.styles import render_captions, CaptionStyle, generate_caption_styles

async def test_clean_ass():
    """Test clean ASS generation and caption burning"""
    print("🧹 TESTING CLEAN ASS GENERATION")
    print("=" * 50)
    
    # Create clean test captions
    test_captions = [
        {"start": 0.0, "end": 2.5, "text": "This room is like a red carpet Hollywood hallway."},
        {"start": 2.5, "end": 4.5, "text": "I say we go to the movie exhibit next."},
        {"start": 4.5, "end": 6.0, "text": "I see some stars, where's my name?"}
    ]
    
    # Generate clean ASS file
    style_config = generate_caption_styles(CaptionStyle.BOXED_HIGH_CONTRAST)
    ass_content = render_captions(test_captions, style_config, "ass")
    
    # Write clean ASS file
    clean_ass_path = "test_clean.ass"
    with open(clean_ass_path, 'w', encoding='utf-8') as f:
        f.write(ass_content)
    
    print(f"✅ Generated clean ASS file: {clean_ass_path}")
    print(f"📄 ASS content preview:")
    print(ass_content[:500] + "..." if len(ass_content) > 500 else ass_content)
    
    # Create a simple test video
    test_video = "test_clean.mp4"
    cmd = [
        "ffmpeg", "-f", "lavfi", 
        "-i", "color=c=blue:size=1080x1920:duration=6",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", 
        "-preset", "ultrafast", "-y", test_video
    ]
    
    print(f"\n🎬 Creating test video...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to create test video: {result.stderr}")
        return
    
    print(f"✅ Test video created: {test_video}")
    
    # Test caption burning
    from app.services.video_processor import VideoProcessor
    
    processor = VideoProcessor()
    
    try:
        print(f"\n🔥 Testing caption burning with clean ASS...")
        result_path = await processor._burn_ass_captions(test_video, clean_ass_path)
        
        if result_path != test_video:
            print(f"✅ Caption burning succeeded: {result_path}")
            
            # Check if output exists
            if os.path.exists(result_path):
                size = os.path.getsize(result_path)
                print(f"📁 Captioned output: {result_path} ({size} bytes)")
                
                # Extract frame to verify
                frame_path = "test_frame.png"
                cmd = [
                    "ffmpeg", "-ss", "1.0", "-i", result_path,
                    "-frames:v", "1", "-y", frame_path
                ]
                subprocess.run(cmd, capture_output=True)
                
                if os.path.exists(frame_path):
                    frame_size = os.path.getsize(frame_path)
                    print(f"📸 Frame extracted: {frame_path} ({frame_size} bytes)")
                    os.remove(frame_path)
            else:
                print(f"❌ Captioned output file not found")
        else:
            print(f"❌ Caption burning failed - returned original video")
            
    except Exception as e:
        print(f"❌ Caption burning error: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    print(f"\n🧹 Cleaning up...")
    for file in [clean_ass_path, test_video]:
        if os.path.exists(file):
            os.remove(file)
            print(f"   Removed: {file}")
    
    print(f"\n✅ Clean ASS test complete!")

if __name__ == "__main__":
    asyncio.run(test_clean_ass())
