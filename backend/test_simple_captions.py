#!/usr/bin/env python3
"""
Simple test script for basic caption burning.
Uses simple text to avoid parsing issues.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.video_processor import VideoProcessor

async def test_simple_captions():
    """Test basic caption burning with simple text"""
    print("🧪 Testing Simple Caption Burning")
    print("=" * 50)
    
    # Test with a real clip if available
    outputs_dir = Path("outputs")
    if outputs_dir.exists():
        mp4_files = list(outputs_dir.glob("*.mp4"))
        if mp4_files:
            # Use the first MP4 file found
            test_video = str(mp4_files[0])
            print(f"\n🎬 Testing with real video: {os.path.basename(test_video)}")
            
            # Create a simple test ASS file with basic text
            test_ass_content = """[Script Info]
ScriptType: v4.00+
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:05.00,Default,,0,0,0,,Hello World Test
Dialogue: 0,0:00:06.00,0:00:10.00,Default,,0,0,0,,Simple Caption Test
"""
            
            # Write test ASS file
            test_ass_file = "test_simple.ass"
            with open(test_ass_file, 'w', encoding='utf-8') as f:
                f.write(test_ass_content)
            
            print(f"📝 Created test ASS file: {test_ass_file}")
            
            try:
                # Initialize video processor
                processor = VideoProcessor()
                
                # Test caption burning
                print("🔥 Testing simple caption burning...")
                result_path = await processor._burn_ass_captions(test_video, test_ass_file, 0.0)
                
                if result_path and result_path != test_video:
                    print(f"✅ Simple caption burning successful!")
                    print(f"📁 Original: {test_video} ({os.path.getsize(test_video)} bytes)")
                    print(f"📁 Captioned: {result_path} ({os.path.getsize(result_path)} bytes)")
                    
                    # Verify the captioned file
                    if await processor._verify_captioned_video(result_path):
                        print("✅ Captioned video verification passed")
                    else:
                        print("❌ Captioned video verification failed")
                    
                    # Test pixel-based verification
                    if await processor._verify_caption_burn_in(test_video, result_path):
                        print("✅ Pixel-based verification passed - captions are visible!")
                    else:
                        print("❌ Pixel-based verification failed - captions not visible")
                    
                else:
                    print("❌ Caption burning failed - returned original path")
                    
            except Exception as e:
                print(f"❌ Caption burning test failed: {e}")
                import traceback
                traceback.print_exc()
            
            # Cleanup test file
            if os.path.exists(test_ass_file):
                os.remove(test_ass_file)
                print(f"🧹 Cleaned up test file: {test_ass_file}")
        else:
            print("⚠️ No MP4 files found in outputs directory")
    else:
        print("⚠️ No outputs directory found")
    
    print("\n" + "=" * 50)
    print("🧪 Simple Caption Test Complete")

if __name__ == "__main__":
    asyncio.run(test_simple_captions())
