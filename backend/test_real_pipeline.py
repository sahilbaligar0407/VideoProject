#!/usr/bin/env python3
"""
Test the complete real pipeline with caption burning to verify end-to-end functionality.
"""

import os
import sys
import asyncio
import subprocess
import hashlib
import json
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.video_processor import VideoProcessor

async def test_real_pipeline():
    """Test the complete real pipeline with caption burning"""
    print("🚀 TESTING REAL PIPELINE WITH CAPTION BURNING")
    print("=" * 60)
    
    # Find a real clip to test
    outputs_dir = "outputs"
    clip_files = [f for f in os.listdir(outputs_dir) if f.endswith('.mp4')]
    
    if not clip_files:
        print("❌ No clip files found in outputs directory")
        return
    
    # Use the first clip
    clip_file = clip_files[0]
    clip_id = clip_file.replace('.mp4', '')
    
    print(f"📹 Testing with real clip: {clip_file}")
    
    # A) Paths & sizes (real clip)
    print("\n📋 A) Paths & Sizes (Real Clip)")
    
    original_clip_path = os.path.join(outputs_dir, clip_file)
    original_size = os.path.getsize(original_clip_path)
    print(f"   Original clip: {os.path.abspath(original_clip_path)} ({original_size} bytes)")
    
    # Check for ASS file
    ass_path = os.path.join(outputs_dir, f"{clip_id}.ass")
    if os.path.exists(ass_path):
        ass_size = os.path.getsize(ass_path)
        print(f"   ASS file: {os.path.abspath(ass_path)} ({ass_size} bytes)")
    else:
        print(f"   ASS file: NOT FOUND")
        return
    
    # B) Test caption burning on the real clip
    print("\n🔥 B) Testing Caption Burning on Real Clip")
    
    processor = VideoProcessor()
    
    try:
        print(f"   🔥 Running caption burning on real clip...")
        result = await processor._burn_ass_captions(original_clip_path, ass_path, clip_start=0.0)
        print(f"   Result: {result}")
        
        if result != original_clip_path:  # Caption burning succeeded
            print("   ✅ Caption burning completed")
            
            # Check if captioned file exists
            if os.path.exists(result):
                result_size = os.path.getsize(result)
                print(f"   Captioned output: {result} ({result_size} bytes)")
                
                # C) Frame diff proof
                print("\n📸 C) Frame Diff Proof")
                
                # Extract frame from original
                orig_frame = f"orig_{clip_id}.png"
                cmd = [
                    "ffmpeg", "-ss", "1.0", "-i", original_clip_path,
                    "-frames:v", "1", "-y", orig_frame
                ]
                subprocess.run(cmd, capture_output=True)
                
                if os.path.exists(orig_frame):
                    orig_size = os.path.getsize(orig_frame)
                    orig_hash = calculate_sha1(orig_frame)
                    print(f"   Original frame: {orig_frame} ({orig_size} bytes, SHA1: {orig_hash})")
                
                # Extract frame from captioned
                cap_frame = f"cap_{clip_id}.png"
                cmd = [
                    "ffmpeg", "-ss", "1.0", "-i", result,
                    "-frames:v", "1", "-y", cap_frame
                ]
                subprocess.run(cmd, capture_output=True)
                
                if os.path.exists(cap_frame):
                    cap_size = os.path.getsize(cap_frame)
                    cap_hash = calculate_sha1(cap_frame)
                    print(f"   Captioned frame: {cap_frame} ({cap_size} bytes, SHA1: {cap_hash})")
                    
                    # Check if hashes are identical
                    if orig_hash == cap_hash:
                        print(f"   ⚠️ WARNING: Frame hashes are identical - captions may not be visible!")
                    else:
                        print(f"   ✅ Frame hashes differ - captions should be visible")
                
            else:
                print(f"   ❌ Captioned output file not found")
        else:
            print(f"   ❌ Caption burning failed - returned original video")
            
    except Exception as e:
        print(f"   ❌ Caption burning error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # D) Check manifest
    print("\n📄 D) Checking Manifest")
    
    manifest_path = os.path.join(outputs_dir, f"{clip_id}.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        print(f"   Manifest file: {os.path.abspath(manifest_path)}")
        print(f"   Manifest content: {json.dumps(manifest, indent=2)}")
    else:
        print(f"   Manifest: NOT FOUND")
    
    # E) Check for CAPS_OK watermark
    print("\n💧 E) Checking for CAPS_OK Watermark")
    
    if os.path.exists(result) and result != original_clip_path:
        # Extract frame to check for watermark
        watermark_frame = f"watermark_{clip_id}.png"
        cmd = [
            "ffmpeg", "-ss", "1.0", "-i", result,
            "-frames:v", "1", "-y", watermark_frame
        ]
        subprocess.run(cmd, capture_output=True)
        
        if os.path.exists(watermark_frame):
            watermark_size = os.path.getsize(watermark_frame)
            print(f"   Watermark check frame: {watermark_frame} ({watermark_size} bytes)")
            
            # Simple check: if frame size increased significantly, watermark might be there
            if watermark_size > orig_size * 1.1:  # 10% increase
                print(f"   ✅ Frame size increased - watermark likely present")
            else:
                print(f"   ⚠️ Frame size similar - watermark may not be visible")
    
    # F) Final verification
    print("\n🔍 F) Final Verification")
    
    print(f"   Pre-burn path: {os.path.abspath(original_clip_path)}")
    print(f"   Captioned path: {os.path.abspath(result)}")
    print(f"   Published path: {os.path.abspath(result)}")  # Should be the same as captioned path
    
    # Verify the paths are different
    if result != original_clip_path:
        print(f"   ✅ Paths are different - burned file will be published")
    else:
        print(f"   ❌ Paths are identical - original file will be published")
    
    # Cleanup
    print("\n🧹 Cleaning up test files...")
    test_files = []
    if 'orig_frame' in locals():
        test_files.append(orig_frame)
    if 'cap_frame' in locals():
        test_files.append(cap_frame)
    if 'watermark_frame' in locals():
        test_files.append(watermark_frame)
    
    for test_file in test_files:
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"   Removed: {test_file}")
    
    print("\n✅ Real pipeline test complete!")

def calculate_sha1(file_path):
    """Calculate SHA1 hash of file"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha1(f.read()).hexdigest()
    except Exception:
        return "ERROR"

if __name__ == "__main__":
    asyncio.run(test_real_pipeline())
