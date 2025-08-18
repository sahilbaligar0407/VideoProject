#!/usr/bin/env python3
"""
MoviePy-based caption system for reliable video caption generation.
This replaces the FFmpeg drawtext approach with MoviePy's more robust text handling.
"""

import os
import json
import tempfile
from typing import List, Dict, Any
from moviepy import TextClip, CompositeVideoClip, ColorClip, VideoFileClip
import numpy as np

def split_text_into_lines(word_data: List[Dict], max_chars: int = 20, max_duration: float = 2.5, max_gap: float = 1.5):
    """
    Split word-level data into subtitle lines based on character count, duration, and gaps.
    
    Args:
        word_data: List of word dictionaries with 'word', 'start', 'end' keys
        max_chars: Maximum characters per line
        max_duration: Maximum duration per line
        max_gap: Maximum gap between words before starting new line
        
    Returns:
        List of subtitle line dictionaries
    """
    subtitles = []
    line = []
    line_duration = 0
    line_chars = 0

    for idx, word_info in enumerate(word_data):
        word = word_info["word"]
        start = word_info["start"]
        end = word_info["end"]
        
        # Debug: print what we're processing
        print(f"      Processing word: '{word}' ({start:.2f}s - {end:.2f}s)")

        line.append(word_info)
        line_duration += end - start

        temp = " ".join(item["word"] for item in line)
        new_line_chars = len(temp)

        # Check if we should start a new line
        duration_exceeded = line_duration > max_duration
        chars_exceeded = new_line_chars > max_chars
        
        if idx > 0:
            gap = word_info['start'] - word_data[idx - 1]['end']
            maxgap_exceeded = gap > max_gap
        else:
            maxgap_exceeded = False

        if duration_exceeded or chars_exceeded or maxgap_exceeded:
            if line:
                subtitle_line = {
                    "text": " ".join(item["word"] for item in line),
                    "start": line[0]["start"],
                    "end": line[-1]["end"],
                    "words": line
                }
                print(f"      Creating line: '{subtitle_line['text']}'")
                subtitles.append(subtitle_line)
                line = []
                line_duration = 0
                line_chars = 0

    # Add the last line if it exists
    if line:
        subtitle_line = {
            "text": " ".join(item["word"] for item in line),
            "start": line[0]["start"],
            "end": line[-1]["end"],
            "words": line
        }
        print(f"      Creating final line: '{subtitle_line['text']}'")
        subtitles.append(subtitle_line)

    return subtitles

def create_caption_clips(subtitle_line: Dict, frame_size: tuple, font_path: str, 
                         fontsize: float, color: str = "white", 
                         highlight_color: str = "yellow", 
                         stroke_color: str = "black", stroke_width: float = 2.6):
    """
    Create MoviePy text clips for a subtitle line with word-level highlighting.
    
    Args:
        subtitle_line: Dictionary with 'text', 'start', 'end', 'words' keys
        frame_size: Video frame size (width, height)
        font_path: Path to the font file
        fontsize: Font size as percentage of frame height
        color: Base text color
        highlight_color: Highlight color for words
        stroke_color: Stroke/outline color
        stroke_width: Stroke width
        
    Returns:
        Tuple of (text_clips, positions)
    """
    word_clips = []
    positions = []
    
    frame_width, frame_height = frame_size
    actual_fontsize = int(frame_height * fontsize / 100)
    
    # Create a single text clip for the entire line (simpler approach)
    full_text = subtitle_line['text']
    start_time = subtitle_line['start']
    end_time = subtitle_line['end']
    duration = end_time - start_time
    
    # Create the main text clip
    text_clip = TextClip(
        text=full_text, 
        font=font_path, 
        font_size=actual_fontsize, 
        color=color,
        stroke_color=stroke_color,
        stroke_width=stroke_width
    ).with_start(start_time).with_duration(duration)
    
    # Store position info for background calculation
    positions.append({
        "x_pos": 0,
        "y_pos": 0,
        "width": text_clip.size[0],
        "height": text_clip.size[1],
        "word": full_text,
        "start": start_time,
        "end": end_time,
        "duration": duration
    })
    
    word_clips.append(text_clip)
    
    return word_clips, positions

def add_captions_to_video(video_path: str, word_data: List[Dict], output_path: str,
                         font_path: str = None, fontsize: float = 4.0, 
                         color: str = "white", highlight_color: str = "yellow",
                         background_opacity: float = 0.0, max_chars: int = 20,
                         position: str = "bottom75"):
    """
    Add captions to video using MoviePy.
    
    Args:
        video_path: Path to input video
        word_data: List of word dictionaries with timing
        output_path: Path for output video
        font_path: Path to font file
        fontsize: Font size as percentage of frame height
        color: Base text color
        highlight_color: Highlight color for words
        background_opacity: Background opacity (0.0 = transparent)
        max_chars: Maximum characters per line
        position: Caption position ("bottom75", "center", "top", "bottom")
        
    Returns:
        Path to output video
    """
    # Load video
    input_video = VideoFileClip(video_path)
    frame_size = input_video.size
    
    # Use default Poppins font if none specified
    if font_path is None:
        font_path = os.path.join("outputs", "Poppins-Bold.ttf")
        if not os.path.exists(font_path):
            # Fallback to system font
            font_path = "C:/Windows/Fonts/arial.ttf"
    
    # Split into subtitle lines
    subtitle_lines = split_text_into_lines(word_data, max_chars)
    print(f"   📝 Split into {len(subtitle_lines)} subtitle lines")
    
    # Debug: show first few lines
    for i, line in enumerate(subtitle_lines[:3]):
        print(f"      Line {i+1}: '{line.get('text', 'N/A')}' ({line.get('start', 0):.2f}s - {line.get('end', 0):.2f}s)")
    
    all_caption_clips = []
    
    for line in subtitle_lines:
        # Create caption clips for this line
        word_clips, positions = create_caption_clips(
            line, frame_size, font_path, fontsize, color, highlight_color
        )
        
        # Safety check: ensure we have valid clips and positions
        if not word_clips or not positions:
            print(f"⚠️ Skipping caption line '{line.get('text', 'N/A')}' - no valid clips generated")
            continue
        
        # Create background if opacity > 0
        if background_opacity > 0 and positions:
            try:
                max_width = max(pos['x_pos'] + pos['width'] for pos in positions)
                max_height = max(pos['y_pos'] + pos['height'] for pos in positions)
                
                # Ensure minimum dimensions
                max_width = max(max_width, 100)
                max_height = max(max_height, 50)
                
                background = ColorClip(
                    size=(int(max_width * 1.1), int(max_height * 1.1)),
                    color=(64, 64, 64)
                ).with_opacity(background_opacity)
                
                background = background.with_start(line['start']).with_duration(line['end'] - line['start'])
                
                # Combine background with text clips
                line_composite = CompositeVideoClip([background] + word_clips)
            except Exception as e:
                print(f"⚠️ Background creation failed for line '{line.get('text', 'N/A')}': {e}")
                line_composite = CompositeVideoClip(word_clips)
        else:
            line_composite = CompositeVideoClip(word_clips)
        
        # Position the caption - use relative positioning for all positions
        if position == "bottom75":
            line_composite = line_composite.with_position(('center', 0.75), relative=True)
        elif position == "center":
            line_composite = line_composite.with_position('center')
        elif position == "top":
            line_composite = line_composite.with_position(('center', 0.1), relative=True)
        elif position == "bottom":
            line_composite = line_composite.with_position(('center', 0.9), relative=True)
        elif position == "bottom80":
            line_composite = line_composite.with_position(('center', 0.80), relative=True)
        else:
            line_composite = line_composite.with_position('center')
        
        # Debug: print positioning info
        print(f"   📍 Positioned caption '{line.get('text', 'N/A')[:50]}' at {position}")
        print(f"      Clip size: {line_composite.size}")
        print(f"      Timing: {line['start']:.2f}s - {line['end']:.2f}s")
        print(f"      Text content: '{line.get('text', 'N/A')}'")
        
        all_caption_clips.append(line_composite)
    
    # Safety check: ensure we have valid caption clips
    if not all_caption_clips:
        print(f"⚠️ No valid caption clips generated, returning original video")
        input_video.close()
        return video_path
    
    print(f"   🎬 Combining {len(all_caption_clips)} caption clips with video...")
    print(f"      Video size: {input_video.size}")
    print(f"      Caption clips: {[clip.size for clip in all_caption_clips[:3]]}")
    
    # Combine video with captions
    final_video = CompositeVideoClip([input_video] + all_caption_clips)
    final_video = final_video.with_audio(input_video.audio)
    
    # Write output
    final_video.write_videofile(
        output_path, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac"
    )
    
    # Clean up
    input_video.close()
    final_video.close()
    
    return output_path

def process_video_with_captions(video_path: str, transcription_data: List[Dict], 
                              clip_id: str = None, **kwargs):
    """
    Main function to process video with captions using MoviePy.
    
    Args:
        video_path: Path to input video
        transcription_data: Transcription segments with word timing
        clip_id: Clip ID for logging
        **kwargs: Additional caption options
        
    Returns:
        Path to captioned video
    """
    # Extract word-level data from transcription
    word_data = []
    
    # Check if we already have word-level data or need to extract from segments
    if transcription_data and 'word' in transcription_data[0]:
        # Already in word-level format
        word_data = transcription_data
        print(f"   📝 Using existing word-level data: {len(word_data)} words")
    else:
        # Extract from segment format
        for segment in transcription_data:
            if 'words' in segment:
                for word in segment['words']:
                    word_data.append({
                        'word': word.get('word', word.get('text', '')),
                        'start': float(word.get('start', segment.get('start', 0.0))),
                        'end': float(word.get('end', segment.get('end', 0.0)))
                    })
            else:
                # Fallback: treat segment as single word
                word_data.append({
                    'word': segment.get('text', ''),
                    'start': float(segment.get('start', 0.0)),
                    'end': float(segment.get('end', 0.0))
                })
        print(f"   📝 Extracted word-level data from segments: {len(word_data)} words")
    
    # Sort by start time
    word_data.sort(key=lambda x: x['start'])
    
    # Generate output path
    output_path = video_path.replace('.mp4', '_captioned.mp4')
    
    # Default caption settings for 9:16 vertical video
    caption_options = {
        'fontsize': 8.0,  # 8% of frame height for reels (doubled from 4%)
        'max_chars': 25,  # 25 chars max for reels (increased from 10)
        'color': 'white',
        'highlight_color': 'yellow',
        'background_opacity': 0.6,  # Semi-transparent black background for visibility
        'position': 'bottom80'  # 80% from top (slightly higher than bottom75)
    }
    
    # Update with any provided options
    caption_options.update(kwargs)
    
    print(f"🎬 Adding captions to {video_path}")
    print(f"🔍 Word count: {len(word_data)}")
    print(f"🔍 Caption options: {caption_options}")
    
    try:
        result_path = add_captions_to_video(
            video_path, word_data, output_path, **caption_options
        )
        print(f"✅ Captions added successfully: {result_path}")
        return result_path
    except Exception as e:
        print(f"❌ Failed to add captions: {e}")
        raise
