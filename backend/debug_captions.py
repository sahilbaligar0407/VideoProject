#!/usr/bin/env python3
"""
Debug script to figure out why captions aren't visible on the generated video.
"""

import os
import json
import sys
from pathlib import Path

# Add the app directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from captions.moviepy_captions import process_video_with_captions

def debug_caption_visibility():
    """Debug why captions aren't visible."""
    
    clip_id = "clip_1_70dbf0b1-e93f-4c66-9998-412afe0b79ca"
    video_path = f"outputs/{clip_id}.mp4"
    json_path = f"outputs/{clip_id}.json"
    captioned_path = f"outputs/{clip_id}_captioned.mp4"
    
    print(f"🔍 Debugging caption visibility for: {clip_id}")
    print("=" * 60)
    
    # 1. Check if files exist
    print("📁 File existence check:")
    print(f"   Original video: {'✅' if os.path.exists(video_path) else '❌'} {video_path}")
    print(f"   JSON data: {'✅' if os.path.exists(json_path) else '❌'} {json_path}")
    print(f"   Captioned video: {'✅' if os.path.exists(captioned_path) else '❌'} {captioned_path}")
    
    # 2. Check font availability
    print("\n🔤 Font availability check:")
    poppins_path = "outputs/Poppins-Bold.ttf"
    arial_path = "C:/Windows/Fonts/arial.ttf"
    
    print(f"   Poppins-Bold.ttf: {'✅' if os.path.exists(poppins_path) else '❌'} {poppins_path}")
    print(f"   Arial fallback: {'✅' if os.path.exists(arial_path) else '❌'} {arial_path}")
    
    # 3. Check video properties
    print("\n🎬 Video properties check:")
    if os.path.exists(video_path):
        try:
            from moviepy import VideoFileClip
            clip = VideoFileClip(video_path)
            print(f"   Frame size: {clip.size}")
            print(f"   Duration: {clip.duration:.2f}s")
            print(f"   FPS: {clip.fps}")
            clip.close()
        except Exception as e:
            print(f"   ❌ Error reading video: {e}")
    
    # 4. Check transcription data
    print("\n📝 Transcription data check:")
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            segments = data.get('segments', [])
            print(f"   Total segments: {len(segments)}")
            
            if segments:
                first_seg = segments[0]
                print(f"   First segment: '{first_seg.get('text', 'N/A')}'")
                print(f"   First timing: {first_seg.get('start', 0):.2f}s - {first_seg.get('end', 0):.2f}s")
                
                last_seg = segments[-1]
                print(f"   Last segment: '{last_seg.get('text', 'N/A')}'")
                print(f"   Last timing: {last_seg.get('start', 0):.2f}s - {last_seg.get('end', 0):.2f}s")
        except Exception as e:
            print(f"   ❌ Error reading JSON: {e}")
    
    # 5. Test with different caption settings
    print("\n🧪 Testing caption generation with different settings:")
    
    if os.path.exists(json_path) and os.path.exists(video_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            segments = data.get('segments', [])
            
            # Convert to word-level data
            word_data = []
            for segment in segments:
                word_data.append({
                    'word': segment['text'],
                    'start': float(segment['start']),
                    'end': float(segment['end'])
                })
            
            # Test with more visible settings
            test_output = f"outputs/{clip_id}_debug_captioned.mp4"
            
            print(f"   🎯 Testing with debug settings...")
            print(f"   📍 Position: center (instead of bottom75)")
            print(f"   🎨 Font size: 8.0 (instead of 4.0)")
            print(f"   🌈 Background: semi-transparent black")
            
            result = process_video_with_captions(
                video_path=video_path,
                transcription_data=word_data,
                clip_id=clip_id,
                fontsize=8.0,  # Much larger font
                max_chars=50,   # Allow longer lines
                color="white",
                highlight_color="yellow",
                background_opacity=0.7,  # Visible background
                position="center"  # Center of screen
            )
            
            if result and os.path.exists(result):
                print(f"   ✅ Debug captioned video created: {result}")
                print(f"   📊 Size: {os.path.getsize(result)} bytes")
                
                # Rename to debug version
                if os.path.exists(test_output):
                    os.remove(test_output)
                os.rename(result, test_output)
                print(f"   🔄 Renamed to: {test_output}")
                
            else:
                print(f"   ❌ Failed to create debug captioned video")
                
        except Exception as e:
            print(f"   ❌ Error in debug caption test: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎯 Next steps:")
    print("1. Check if the debug captioned video has visible captions")
    print("2. If yes, the issue was positioning/sizing")
    print("3. If no, there's a deeper issue with the caption system")

if __name__ == "__main__":
    debug_caption_visibility()
