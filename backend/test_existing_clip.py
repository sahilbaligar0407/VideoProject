#!/usr/bin/env python3
"""
Test the MoviePy caption system on an existing clip to verify it's working.
"""

import os
import json
import sys

# Add the app directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from captions.moviepy_captions import process_video_with_captions

def test_existing_clip():
    """Test caption generation on an existing clip."""
    
    # Paths to existing clip files
    clip_id = "clip_1_70dbf0b1-e93f-4c66-9998-412afe0b79ca"
    video_path = f"outputs/{clip_id}.mp4"
    json_path = f"outputs/{clip_id}.json"
    
    print(f"🎬 Testing MoviePy captions on existing clip: {clip_id}")
    print(f"📁 Video path: {video_path}")
    print(f"📁 JSON path: {json_path}")
    
    # Check if files exist
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        return False
    
    # Load transcription data
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            clip_data = json.load(f)
        
        segments = clip_data.get('segments', [])
        print(f"✅ Loaded {len(segments)} transcription segments")
        
        # Convert segments to word-level data for MoviePy
        word_data = []
        for segment in segments:
            # For now, treat each segment as a single word with timing
            # In a real scenario, you'd have word-level timing from Whisper
            word_data.append({
                'word': segment['text'],
                'start': float(segment['start']),
                'end': float(segment['end'])
            })
        
        print(f"🔍 Converted to {len(word_data)} word-level entries")
        
        # Test the MoviePy caption system
        print(f"🎬 Processing video with MoviePy captions...")
        
        result_path = process_video_with_captions(
            video_path=video_path,
            transcription_data=word_data,
            clip_id=clip_id
            # Use the new improved defaults: fontsize=8.0, background_opacity=0.6, position=bottom80
        )
        
        if result_path and os.path.exists(result_path):
            print(f"✅ SUCCESS! Captioned video created: {result_path}")
            print(f"📊 File size: {os.path.getsize(result_path)} bytes")
            print(f"📊 Original size: {os.path.getsize(video_path)} bytes")
            return True
        else:
            print(f"❌ Failed to create captioned video")
            return False
            
    except Exception as e:
        print(f"❌ Error processing clip: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing MoviePy Caption System on Existing Clip")
    print("=" * 60)
    
    success = test_existing_clip()
    
    if success:
        print("\n🎉 SUCCESS! The MoviePy caption system is working!")
        print("📝 You should now see a '_captioned.mp4' file in the outputs folder.")
    else:
        print("\n💥 FAILED! There's still an issue with the caption system.")
    
    print("\n" + "=" * 60)
