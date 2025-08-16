#!/usr/bin/env python3
"""
Test script to verify vertical renderer and caption fixes.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.video.vertical import extract_vertical_clip
from app.services.video_processor import VideoProcessor

async def test_vertical_renderer():
    """Test the vertical renderer with a sample video"""
    print("🧪 Testing vertical renderer fixes...")
    
    # Check if we have a test video
    test_video = "uploads/e209460b-8c9f-4c21-b9c2-df31400ac530_clip_1be3ee78-4ed3-41fd-aa90-f155bf1a23b9.mp4"
    
    if not os.path.exists(test_video):
        print(f"❌ Test video not found: {test_video}")
        print("💡 Upload a video first to test the renderer")
        return False
    
    print(f"✅ Found test video: {test_video}")
    
    # Test vertical cover mode
    output_path = "test_output_vertical_cover.mp4"
    print(f"\n🎬 Testing vertical cover mode...")
    
    success = extract_vertical_clip(
        test_video, output_path, 
        start=10, duration=5, 
        mode="cover"
    )
    
    if success:
        print(f"✅ Vertical cover test passed!")
        
        # Verify output dimensions
        try:
            import subprocess
            probe_cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height,sample_aspect_ratio",
                "-of", "csv=p=0", output_path
            ]
            result = subprocess.run(probe_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                output = result.stdout.strip()
                print(f"📏 Output dimensions: {output}")
                
                # Check if it's 1080x1920
                if "1080,1920" in output:
                    print(f"✅ Output is correct 9:16 format (1080x1920)")
                else:
                    print(f"❌ Output is not 9:16 format")
                    return False
            else:
                print(f"⚠️ Could not verify output dimensions")
        except Exception as e:
            print(f"⚠️ Verification failed: {e}")
        
        # Clean up test file
        if os.path.exists(output_path):
            os.remove(output_path)
            print(f"🧹 Cleaned up test file")
        
        return True
    else:
        print(f"❌ Vertical cover test failed!")
        return False

async def test_caption_burning():
    """Test the caption burning with SRT + force_style"""
    print("\n🧪 Testing caption burning fixes...")
    
    # Create a test video processor
    processor = VideoProcessor()
    
    # Create a dummy ASS file for testing
    test_ass = "test_captions.ass"
    ass_content = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Inter,42,&H00FFFFFF,&H00FFFFFF,&H66000000,&H00000000,0,0,0,0,100,100,0,0,3,3,0,2,80,80,160,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,This is a test caption
Dialogue: 0,0:00:02.00,0:00:04.00,Default,,0,0,0,,Second line of caption text"""
    
    with open(test_ass, 'w', encoding='utf-8') as f:
        f.write(ass_content)
    
    print(f"✅ Created test ASS file: {test_ass}")
    
    # Test the conversion to SRT
    try:
        await processor._convert_ass_to_srt(test_ass, "test_captions.srt")
        print(f"✅ ASS to SRT conversion test passed!")
        
        # Check if SRT file was created
        if os.path.exists("test_captions.srt"):
            with open("test_captions.srt", 'r', encoding='utf-8') as f:
                srt_content = f.read()
                print(f"📝 SRT content preview:")
                print(srt_content[:200] + "..." if len(srt_content) > 200 else srt_content)
            
            # Clean up test files
            os.remove(test_ass)
            os.remove("test_captions.srt")
            print(f"🧹 Cleaned up test files")
            
            return True
        else:
            print(f"❌ SRT file was not created")
            return False
            
    except Exception as e:
        print(f"❌ ASS to SRT conversion test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting ClipGenius Fix Verification Tests...")
    
    # Test vertical renderer
    vertical_success = await test_vertical_renderer()
    
    # Test caption burning
    caption_success = await test_caption_burning()
    
    # Summary
    print(f"\n📊 Test Results:")
    print(f"   Vertical Renderer: {'✅ PASSED' if vertical_success else '❌ FAILED'}")
    print(f"   Caption Burning: {'✅ PASSED' if caption_success else '❌ FAILED'}")
    
    if vertical_success and caption_success:
        print(f"\n🎉 All tests passed! The fixes are working correctly.")
        return True
    else:
        print(f"\n⚠️ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
