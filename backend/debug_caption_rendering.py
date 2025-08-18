#!/usr/bin/env python3
"""
Debug script to figure out why captions aren't rendering even though background is visible.
"""

import os
import json
import sys

# Add the app directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from captions.moviepy_captions import process_video_with_captions, split_text_into_lines, create_caption_clips

def debug_caption_rendering():
    """Debug why captions aren't rendering."""
    
    clip_id = "clip_1_6613faa6-b6ce-410d-885b-0f0ba58390c3"
    video_path = f"outputs/{clip_id}.mp4"
    json_path = f"outputs/{clip_id}.json"
    
    print(f"🔍 Debugging caption rendering for: {clip_id}")
    print("=" * 70)
    
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
            word_data.append({
                'word': segment['text'],
                'start': float(segment['start']),
                'end': float(segment['end'])
            })
        
        print(f"🔍 Converted to {len(word_data)} word-level entries")
        
        # Test the text splitting function
        print(f"\n🧪 Testing text splitting function...")
        subtitle_lines = split_text_into_lines(word_data, max_chars=25)
        print(f"   📝 Generated {len(subtitle_lines)} subtitle lines")
        
        for i, line in enumerate(subtitle_lines[:3]):  # Show first 3 lines
            print(f"   Line {i+1}: '{line['text']}' ({line['start']:.2f}s - {line['end']:.2f}s)")
            print(f"      Words: {len(line['words'])}")
        
        # Test caption clip creation for first line
        if subtitle_lines:
            print(f"\n🧪 Testing caption clip creation for first line...")
            first_line = subtitle_lines[0]
            
            # Get video dimensions
            from moviepy import VideoFileClip
            clip = VideoFileClip(video_path)
            frame_size = clip.size
            clip.close()
            
            print(f"   🎬 Frame size: {frame_size}")
            
            # Test font path
            font_path = os.path.join("outputs", "Poppins-Bold.ttf")
            print(f"   🔤 Font path: {font_path}")
            print(f"   🔤 Font exists: {'✅' if os.path.exists(font_path) else '❌'}")
            
            # Test caption clip creation
            try:
                word_clips, positions = create_caption_clips(
                    first_line, frame_size, font_path, 
                    fontsize=8.0, color="white", highlight_color="yellow"
                )
                
                print(f"   ✅ Generated {len(word_clips)} word clips")
                print(f"   📍 Generated {len(positions)} position records")
                
                if positions:
                    for i, pos in enumerate(positions[:3]):
                        print(f"      Position {i+1}: {pos['word']} at ({pos['x_pos']}, {pos['y_pos']})")
                        print(f"         Size: {pos['width']}x{pos['height']}")
                        print(f"         Timing: {pos['start']:.2f}s - {pos['end']:.2f}s")
                
            except Exception as e:
                print(f"   ❌ Caption clip creation failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Test with a very simple caption to isolate the issue
        print(f"\n🧪 Testing with ultra-simple caption...")
        simple_data = [
            {
                'word': 'TEST',
                'start': 1.0,
                'end': 3.0
            }
        ]
        
        test_output = f"outputs/{clip_id}_ultra_simple.mp4"
        
        try:
            result = process_video_with_captions(
                video_path=video_path,
                transcription_data=simple_data,
                clip_id=clip_id,
                fontsize=15.0,  # Very large font
                max_chars=10,
                color="red",     # Bright red color
                highlight_color="yellow",
                background_opacity=0.8,  # Very visible background
                position="center"  # Center of screen
            )
            
            if result and os.path.exists(result):
                print(f"   ✅ Ultra-simple captioned video created: {result}")
                print(f"   📊 Size: {os.path.getsize(result)} bytes")
                
                # Rename to test version
                if os.path.exists(test_output):
                    os.remove(test_output)
                os.rename(result, test_output)
                print(f"   🔄 Renamed to: {test_output}")
                
                print(f"\n🎯 Now check if '{test_output}' has a visible red 'TEST' caption!")
                print(f"   - Should show 'TEST' in bright red")
                print(f"   - Should be very large and centered")
                print(f"   - Should appear at 1-3 seconds")
                
            else:
                print(f"   ❌ Failed to create ultra-simple captioned video")
                
        except Exception as e:
            print(f"   ❌ Error in ultra-simple caption test: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Error in debug: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("🎯 Next steps:")
    print("1. Check if the ultra-simple video has visible captions")
    print("2. If yes, the issue is with complex caption processing")
    print("3. If no, there's a fundamental issue with text rendering")

if __name__ == "__main__":
    debug_caption_rendering()
