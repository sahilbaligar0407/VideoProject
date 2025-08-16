#!/usr/bin/env python3
"""
Debug script for caption burning with verbose output.
Run with: DEBUG_CAPTIONS=1 python debug_captions.py
"""

import os
import sys
import asyncio
import tempfile
import hashlib
import subprocess
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.video_processor import VideoProcessor
from app.captions.styles import render_captions, CaptionStyle

async def debug_caption_burning():
    """Debug caption burning with verbose output"""
    print("🔍 DEBUG: Caption Burning Diagnostic")
    print("=" * 50)
    
    # Set debug environment
    os.environ['DEBUG_CAPTIONS'] = '1'
    
    # Create a simple test video (2-3 seconds solid color)
    print("\n📹 Step 1: Creating test video...")
    test_video = create_test_video()
    print(f"✅ Test video created: {test_video}")
    print(f"   Size: {os.path.getsize(test_video)} bytes")
    
    # Create a simple test SRT
    print("\n📝 Step 2: Creating test SRT...")
    test_srt = create_test_srt()
    print(f"✅ Test SRT created: {test_srt}")
    print(f"   Size: {os.path.getsize(test_srt)} bytes")
    
    # Show SRT content and validation
    print("\n📋 SRT Content (first 20 lines):")
    with open(test_srt, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')[:20]
        for i, line in enumerate(lines, 1):
            print(f"   {i:2d}: {repr(line)}")
    
    # Validate SRT
    print("\n✅ SRT Validation:")
    srt_valid = validate_srt(test_srt)
    print(f"   Valid: {srt_valid}")
    
    # Show file details
    print(f"\n📊 File Details:")
    print(f"   SRT Path: {os.path.abspath(test_srt)}")
    print(f"   SRT SHA1: {calculate_sha1(test_srt)}")
    print(f"   Encoding: UTF-8 (no BOM)")
    
    # Test caption burning
    print("\n🎬 Step 3: Testing caption burning...")
    processor = VideoProcessor()
    
    # Create a dummy ASS file (since the function expects it)
    test_ass = test_srt.replace('.srt', '.ass')
    with open(test_ass, 'w', encoding='utf-8') as f:
        f.write("""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF&,&H00FFFFFF&,&H00000000&,&H80000000&,0,0,0,0,100,100,0,0,1,2,0,2,80,80,160,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,Hello world
Dialogue: 0,0:00:03.00,0:00:05.00,Default,,0,0,0,,This is a test caption
""")
    
    print(f"✅ Test ASS created: {test_ass}")
    
    # Run caption burning with verbose logging
    print("\n🔥 Running caption burning...")
    try:
        result = await processor._burn_ass_captions(test_video, test_ass)
        print(f"✅ Caption burning result: {result}")
    except Exception as e:
        print(f"❌ Caption burning failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    for file in [test_video, test_srt, test_ass]:
        if os.path.exists(file):
            os.remove(file)
            print(f"   Removed: {file}")
    
    print("\n✅ Debug complete!")

def create_test_video():
    """Create a simple 3-second solid color test video"""
    output_path = "test_video.mp4"
    
    # Create a simple solid color video using FFmpeg
    cmd = [
        "ffmpeg", "-f", "lavfi", "-i", "color=c=red:size=1080x1920:duration=3",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
        "-y", output_path
    ]
    
    print(f"   Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"   ❌ FFmpeg failed: {result.stderr}")
        # Create a dummy file for testing
        with open(output_path, 'w') as f:
            f.write("dummy video content")
        return output_path
    
    return output_path

def create_test_srt():
    """Create a simple test SRT file"""
    output_path = "test_captions.srt"
    
    srt_content = """1
00:00:00,000 --> 00:00:02,000
Hello world

2
00:00:03,000 --> 00:00:05,000
This is a test caption

3
00:00:06,000 --> 00:00:08,000
Short text
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    
    return output_path

def validate_srt(srt_path):
    """Validate SRT file format"""
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic SRT validation
        lines = content.strip().split('\n')
        if len(lines) < 3:
            return False
        
        # Check structure
        i = 0
        while i < len(lines):
            # Should have caption number
            if not lines[i].strip().isdigit():
                return False
            i += 1
            
            # Should have timing
            if i >= len(lines) or ' --> ' not in lines[i]:
                return False
            i += 1
            
            # Should have text
            if i >= len(lines):
                return False
            i += 1
            
            # Should have empty line separator (except for last caption)
            if i < len(lines) and lines[i].strip() != '':
                return False
            i += 1
        
        return True
        
    except Exception as e:
        print(f"   Validation error: {e}")
        return False

def calculate_sha1(file_path):
    """Calculate SHA1 hash of file"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha1(f.read()).hexdigest()
    except Exception:
        return "ERROR"

if __name__ == "__main__":
    asyncio.run(debug_caption_burning())
