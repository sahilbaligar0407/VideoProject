#!/usr/bin/env python3
"""
Test script for visible caption burning with guaranteed visibility.
Tests the new drawbox background and clamped positioning system.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.video_processor import VideoProcessor
from app.captions.burn_drawtext import build_visible_caption_test

async def test_visible_captions():
    """Test the new visible caption system"""
    print("🧪 Testing Visible Caption System")
    print("=" * 50)
    
    # Initialize video processor
    processor = VideoProcessor()
    
    # Test the new caption filter builder
    print("\n🔧 Testing visible caption filter builder...")
    test_filter = build_visible_caption_test("TEST CAPTION TEXT", 0.0, 6.0)
    print(f"Generated filter: {test_filter}")
    
    # Check if filter contains required elements
    required_elements = [
        "format=yuv420p",
        "drawbox",
        "drawtext",
        "CAPS_OK"
    ]
    
    for element in required_elements:
        if element in test_filter:
            print(f"✅ Found {element}")
        else:
            print(f"❌ Missing {element}")
    
    # Test with a real clip if available
    outputs_dir = Path("outputs")
    if outputs_dir.exists():
        mp4_files = list(outputs_dir.glob("*.mp4"))
        if mp4_files:
            # Use the first MP4 file found
            test_video = str(mp4_files[0])
            print(f"\n🎬 Testing with real video: {os.path.basename(test_video)}")
            
            # Check if there's an ASS file for this video
            base_name = test_video.replace(".mp4", "")
            ass_file = base_name + ".ass"
            
            if os.path.exists(ass_file):
                print(f"📝 Found ASS file: {os.path.basename(ass_file)}")
                
                try:
                    # Test caption burning
                    print("🔥 Testing caption burning...")
                    result_path = await processor._burn_ass_captions(test_video, ass_file, 0.0)
                    
                    if result_path and result_path != test_video:
                        print(f"✅ Caption burning successful!")
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
            else:
                print(f"⚠️ No ASS file found for {os.path.basename(test_video)}")
        else:
            print("⚠️ No MP4 files found in outputs directory")
    else:
        print("⚠️ No outputs directory found")
    
    print("\n" + "=" * 50)
    print("🧪 Visible Caption Test Complete")

if __name__ == "__main__":
    asyncio.run(test_visible_captions())
