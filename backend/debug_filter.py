#!/usr/bin/env python3
"""
Debug script to test SRT parsing and filter building step by step.
"""

import os
import sys
import asyncio

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.video_processor import VideoProcessor
from app.captions.burn_drawtext import build_drawtext_filter, validate_filter_string

async def debug_filter_building():
    """Debug the filter building process step by step"""
    print("🔍 DEBUGGING FILTER BUILDING PROCESS")
    print("=" * 50)
    
    # Find a real clip and ASS file
    outputs_dir = "outputs"
    clip_files = [f for f in os.listdir(outputs_dir) if f.endswith('.mp4')]
    
    if not clip_files:
        print("❌ No clip files found")
        return
    
    clip_name = clip_files[0]
    clip_path = os.path.join(outputs_dir, clip_name)
    base_noext = os.path.splitext(clip_path)[0]
    ass_path = base_noext + ".ass"
    
    print(f"📹 Using clip: {clip_name}")
    print(f"📝 ASS file: {ass_path}")
    
    if not os.path.exists(ass_path):
        print(f"❌ ASS file not found: {ass_path}")
        return
    
    # Initialize processor
    processor = VideoProcessor()
    
    # Step 1: Convert ASS to SRT
    print("\n🔄 Step 1: Converting ASS to SRT")
    srt_path = ass_path.replace(".ass", ".srt")
    await processor._convert_ass_to_srt(ass_path, srt_path)
    
    if not os.path.exists(srt_path):
        print("❌ SRT conversion failed")
        return
    
    print(f"✅ SRT created: {srt_path}")
    
    # Step 2: Parse SRT
    print("\n📖 Step 2: Parsing SRT file")
    captions = await processor._parse_srt_file(srt_path)
    
    print(f"📊 Found {len(captions)} captions:")
    for i, caption in enumerate(captions[:5]):  # Show first 5
        print(f"   {i+1}. {caption['start']} -> {caption['end']}: {caption['text'][:50]}...")
    
    if len(captions) > 5:
        print(f"   ... and {len(captions) - 5} more")
    
    # Step 3: Build filter string
    print("\n🔧 Step 3: Building drawtext filter")
    clip_start = 0.0
    
    try:
        vf_value = build_drawtext_filter(
            clip_start=clip_start,
            segments=captions,
            style="poppins_bold_boxed",
            debug_watermark=False
        )
        
        print(f"✅ Filter string built successfully")
        print(f"📏 Filter length: {len(vf_value)} characters")
        print(f"🔍 First 200 chars: {vf_value[:200]}...")
        
        # Step 4: Validate filter string
        print("\n✅ Step 4: Validating filter string")
        is_valid = validate_filter_string(vf_value)
        print(f"🔍 Filter validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
        
        # Step 5: Check for common issues
        print("\n🔍 Step 5: Checking for common issues")
        
        # Check for duplicate drawtext=
        drawtext_count = vf_value.count("drawtext=")
        print(f"   drawtext= count: {drawtext_count}")
        
        # Check for malformed enable expressions
        if ":enable=" in vf_value:
            print("   ⚠️ Found ':enable=' - potential issue")
        
        # Check for missing commas
        if ",," in vf_value:
            print("   ❌ Found double commas - malformed filter")
        
        # Check for empty filters
        filters = vf_value.split(",")
        empty_filters = [f for f in filters if not f.strip()]
        if empty_filters:
            print(f"   ❌ Found {len(empty_filters)} empty filters")
        
        # Step 6: Show individual filters
        print("\n🔍 Step 6: Individual filters")
        # Don't split on commas - FFmpeg filter parameters use colons, multiple filters use commas
        # The filter string should be passed to FFmpeg as-is
        print(f"   Complete filter string: {vf_value}")
        
        # Count drawtext filters by looking for 'drawtext=' occurrences
        drawtext_count = vf_value.count("drawtext=")
        print(f"   Number of drawtext filters: {drawtext_count}")
        
        # Check for basic syntax issues
        if "drawtext=" not in vf_value:
            print("   ❌ Missing 'drawtext=' prefix")
        
        if ":enable=" not in vf_value:
            print("   ❌ Missing ':enable=' parameter")
        
        if ":x=" not in vf_value:
            print("   ❌ Missing ':x=' parameter")
        
        if ":y=" not in vf_value:
            print("   ❌ Missing ':y=' parameter")
        
        if ":fontsize=" not in vf_value:
            print("   ❌ Missing ':fontsize=' parameter")
        
    except Exception as e:
        print(f"❌ Filter building failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_filter_building())
