"""
AutoCaptions service wrapper for integrating the AutoCaptions repository.
This service handles caption generation with customizable styles.
"""

import os
import subprocess
import json
import tempfile
from typing import Dict, Optional, Any
from pathlib import Path
from app.settings import settings


class WordStyle:
    """Style configuration for a specific word type"""
    def __init__(
        self,
        font_family: str = "Arial",
        font_size: int = 32,
        color: str = "yellow",
        bold: bool = False,
        italic: bool = False
    ):
        self.font_family = font_family
        self.font_size = font_size
        self.color = color
        self.bold = bold
        self.italic = italic
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "color": self.color,
            "bold": self.bold,
            "italic": self.italic
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WordStyle":
        return cls(
            font_family=data.get("font_family", "Arial"),
            font_size=data.get("font_size", 32),
            color=data.get("color", "yellow"),
            bold=data.get("bold", False),
            italic=data.get("italic", False)
        )


class CaptionStyle:
    """Caption style configuration with support for wow/like/regular words"""
    def __init__(
        self,
        enabled: bool = True,
        position: str = "bottom",
        regular_words: Optional[WordStyle] = None,
        wow_words: Optional[WordStyle] = None,
        like_words: Optional[WordStyle] = None,
        # Legacy support
        font_family: Optional[str] = None,
        font_size: Optional[int] = None,
        text_color: Optional[str] = None,
        stroke_color: str = "black",
        stroke_width: int = 2,
        max_chars_per_line: int = 42,
        line_spacing: int = 5
    ):
        self.enabled = enabled
        self.position = position
        self.regular_words = regular_words or WordStyle(
            font_family=font_family or "Arial",
            font_size=font_size or 32,
            color=text_color or "yellow"
        )
        self.wow_words = wow_words or WordStyle(
            font_family=font_family or "Impact",
            font_size=(font_size or 32) + 4,
            color=text_color or "yellow",
            bold=True
        )
        self.like_words = like_words or WordStyle(
            font_family=font_family or "Arial",
            font_size=font_size or 32,
            color="green",
            italic=True
        )
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.max_chars_per_line = max_chars_per_line
        self.line_spacing = line_spacing
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "enabled": self.enabled,
            "position": self.position,
            "regular_words": self.regular_words.to_dict(),
            "wow_words": self.wow_words.to_dict(),
            "like_words": self.like_words.to_dict(),
            "stroke_color": self.stroke_color,
            "stroke_width": self.stroke_width,
            "max_chars_per_line": self.max_chars_per_line,
            "line_spacing": self.line_spacing
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CaptionStyle":
        """Create CaptionStyle from dictionary"""
        return cls(
            enabled=data.get("enabled", True),
            position=data.get("position", "bottom"),
            regular_words=WordStyle.from_dict(data.get("regular_words", {})),
            wow_words=WordStyle.from_dict(data.get("wow_words", {})),
            like_words=WordStyle.from_dict(data.get("like_words", {}))
        )


class AutoCaptionsService:
    """Service for adding captions to videos using AutoCaptions repository"""
    
    def __init__(self, autocaptions_path: Optional[str] = None):
        """
        Initialize AutoCaptions service
        
        Args:
            autocaptions_path: Path to AutoCaptions repository. 
                              If None, will try to find it relative to backend directory
        """
        if autocaptions_path:
            self.autocaptions_path = Path(autocaptions_path)
        else:
            # Try to find AutoCaptions relative to backend directory
            backend_dir = Path(__file__).parent.parent.parent
            self.autocaptions_path = backend_dir / "AutoCaptions"
        
        # Check if AutoCaptions exists - look for the run_builder_moviepy.py script
        script_path = self.autocaptions_path / "AutoCaptions" / "tools" / "run_builder_moviepy.py"
        self.use_autocaptions = script_path.exists()
        
        if not self.use_autocaptions:
            print(f"⚠️ AutoCaptions script not found at {script_path}")
            print("   Will use FFmpeg directly for caption burning")
        else:
            print(f"✅ AutoCaptions found at {script_path}")
    
    def add_captions(
        self,
        input_video_path: str,
        transcript_path: str,
        style: CaptionStyle,
        output_path: Optional[str] = None
    ) -> str:
        """
        Add captions to a video using AutoCaptions or FFmpeg
        
        Args:
            input_video_path: Path to input video (segmented clip)
            transcript_path: Path to transcript file (.srt, .vtt, or .ass)
            style: CaptionStyle object with styling options
            output_path: Optional output path. If None, will create next to input video
            
        Returns:
            Path to captioned video
        """
        if not os.path.exists(input_video_path):
            raise FileNotFoundError(f"Input video not found: {input_video_path}")
        
        if not os.path.exists(transcript_path):
            raise FileNotFoundError(f"Transcript file not found: {transcript_path}")
        
        # Determine output path
        if output_path is None:
            base_path = os.path.splitext(input_video_path)[0]
            output_path = f"{base_path}_captioned.mp4"
        
        # Use AutoCaptions if available, otherwise fall back to FFmpeg
        if self.use_autocaptions:
            return self._add_captions_with_autocaptions(input_video_path, transcript_path, style, output_path)
        else:
            return self._add_captions_with_ffmpeg(input_video_path, transcript_path, style, output_path)
    
    def _add_captions_with_autocaptions(
        self,
        input_video_path: str,
        transcript_path: str,
        style: CaptionStyle,
        output_path: str
    ) -> str:
        """Add captions using AutoCaptions Python script with hard-coded styling"""
        try:
            # Use the run_builder_moviepy.py script
            script_path = self.autocaptions_path / "AutoCaptions" / "tools" / "run_builder_moviepy.py"
            
            if not script_path.exists():
                print(f"⚠️ AutoCaptions script not found at {script_path}")
                print("   Falling back to FFmpeg...")
                return self._add_captions_with_ffmpeg(input_video_path, transcript_path, style, output_path)
            
            # Create log file path
            log_dir = self.autocaptions_path / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"{Path(output_path).stem}.log"
            
            # Build command arguments - AutoCaptions uses hard-coded styling
            # The script expects: --video, --subs, --out, --log
            cmd = [
                "python",
                str(script_path),
                "--video", input_video_path,
                "--subs", transcript_path,
                "--out", output_path,
                "--log", str(log_file),
            ]
            
            print(f"🎬 Running AutoCaptions: {' '.join(cmd)}")
            print(f"   Using hard-coded styling from AutoCaptions repository")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for video processing
            )
            
            if result.returncode != 0:
                print(f"❌ AutoCaptions failed: {result.stderr}")
                if result.stdout:
                    print(f"   stdout: {result.stdout[:500]}")
                # Fall back to FFmpeg
                print("   Falling back to FFmpeg...")
                return self._add_captions_with_ffmpeg(input_video_path, transcript_path, style, output_path)
            
            if os.path.exists(output_path):
                print(f"✅ Captions added successfully: {output_path}")
                return output_path
            else:
                raise Exception("AutoCaptions completed but output file not found")
                
        except subprocess.TimeoutExpired:
            print("❌ AutoCaptions timed out, falling back to FFmpeg...")
            return self._add_captions_with_ffmpeg(input_video_path, transcript_path, style, output_path)
        except Exception as e:
            print(f"❌ AutoCaptions error: {e}, falling back to FFmpeg...")
            import traceback
            traceback.print_exc()
            return self._add_captions_with_ffmpeg(input_video_path, transcript_path, style, output_path)
    
    def _add_captions_with_ffmpeg(
        self,
        input_video_path: str,
        transcript_path: str,
        style: CaptionStyle,
        output_path: str
    ) -> str:
        """
        Add captions using FFmpeg directly (fallback method)
        Supports SRT, VTT, and ASS subtitle formats
        """
        try:
            transcript_ext = os.path.splitext(transcript_path)[1].lower()
            
            # Convert color names to hex if needed
            text_color_hex = self._color_to_hex(style.text_color)
            stroke_color_hex = self._color_to_hex(style.stroke_color)
            
            if transcript_ext == ".ass":
                # ASS files already contain styling, just burn them in
                cmd = [
                    "ffmpeg",
                    "-i", input_video_path,
                    "-vf", f"subtitles={transcript_path}:force_style='Fontsize={style.font_size},PrimaryColour={text_color_hex},OutlineColour={stroke_color_hex},Outline={style.stroke_width}'",
                    "-c:a", "copy",
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "23",
                    "-y",
                    output_path
                ]
            elif transcript_ext in [".srt", ".vtt"]:
                # For SRT/VTT, we need to create an ASS file with styling
                ass_path = self._convert_to_ass(transcript_path, style)
                
                cmd = [
                    "ffmpeg",
                    "-i", input_video_path,
                    "-vf", f"subtitles={ass_path}:force_style='Fontsize={style.font_size},PrimaryColour={text_color_hex},OutlineColour={stroke_color_hex},Outline={style.stroke_width}'",
                    "-c:a", "copy",
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "23",
                    "-y",
                    output_path
                ]
            else:
                raise ValueError(f"Unsupported transcript format: {transcript_ext}")
            
            print(f"🎬 Running FFmpeg for caption burning: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                print(f"❌ FFmpeg caption burning failed: {result.stderr}")
                raise Exception(f"FFmpeg failed: {result.stderr}")
            
            if os.path.exists(output_path):
                print(f"✅ Captions burned successfully: {output_path}")
                return output_path
            else:
                raise Exception("FFmpeg completed but output file not found")
                
        except Exception as e:
            print(f"❌ FFmpeg caption burning error: {e}")
            raise
    
    def _convert_to_ass(self, transcript_path: str, style: CaptionStyle) -> str:
        """Convert SRT or VTT to ASS format with styling"""
        try:
            # Read SRT/VTT file
            with open(transcript_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse and convert to ASS
            ass_path = os.path.splitext(transcript_path)[0] + "_styled.ass"
            
            # Create ASS header with styling
            text_color_hex = self._color_to_hex(style.text_color)
            stroke_color_hex = self._color_to_hex(style.stroke_color)
            
            ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style.font_family},{style.font_size},{text_color_hex},&H000000FF,{stroke_color_hex},&H80000000,1,0,0,0,100,100,0,0,1,{style.stroke_width},1,2,40,40,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
            
            # Parse SRT/VTT and convert to ASS Dialogue lines
            # This is a simplified parser - for production, use a proper subtitle library
            lines = content.split('\n')
            dialogue_lines = []
            current_subtitle = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if it's a timestamp line (SRT: "00:00:00,000 --> 00:00:05,000" or VTT: "00:00:00.000 --> 00:00:05.000")
                if '-->' in line:
                    # Parse timestamp
                    parts = line.split('-->')
                    if len(parts) == 2:
                        start_time = self._parse_timestamp(parts[0].strip())
                        end_time = self._parse_timestamp(parts[1].strip())
                        current_subtitle = {
                            'start': start_time,
                            'end': end_time,
                            'text': ''
                        }
                elif current_subtitle and not line.isdigit():
                    # Text line
                    if current_subtitle['text']:
                        current_subtitle['text'] += ' ' + line
                    else:
                        current_subtitle['text'] = line
                    
                    # Check if next line is empty or timestamp (end of subtitle)
                    # For simplicity, we'll add it when we see the next timestamp or end
                    dialogue_lines.append(current_subtitle)
                    current_subtitle = None
            
            # Add dialogue lines
            for sub in dialogue_lines:
                start_ass = self._seconds_to_ass_time(sub['start'])
                end_ass = self._seconds_to_ass_time(sub['end'])
                text = sub['text'].replace('\n', '\\N')
                ass_content += f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,260,,{text}\n"
            
            # Write ASS file
            with open(ass_path, 'w', encoding='utf-8') as f:
                f.write(ass_content)
            
            return ass_path
            
        except Exception as e:
            print(f"⚠️ Failed to convert to ASS, using original file: {e}")
            return transcript_path
    
    def _parse_timestamp(self, timestamp: str) -> float:
        """Parse SRT/VTT timestamp to seconds"""
        # Remove HTML tags if present
        timestamp = timestamp.split('<')[0].strip()
        
        # Handle both SRT (comma) and VTT (dot) formats
        if ',' in timestamp:
            timestamp = timestamp.replace(',', '.')
        
        parts = timestamp.split(':')
        if len(parts) == 3:
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        return 0.0
    
    def _seconds_to_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format (H:MM:SS.cc)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"
    
    def _color_to_hex(self, color: str) -> str:
        """Convert color name or hex to ASS color format (&HBBGGRR&)"""
        color_map = {
            "white": "&H00FFFFFF&",
            "yellow": "&H0000FFFF&",
            "green": "&H0000FF00&",
            "black": "&H00000000&",
            "red": "&H000000FF&",
            "blue": "&H00FF0000&",
        }
        
        color_lower = color.lower()
        if color_lower in color_map:
            return color_map[color_lower]
        
        # If it's already a hex color, convert to ASS format
        if color.startswith("#"):
            hex_color = color[1:]
            if len(hex_color) == 6:
                # Convert #RRGGBB to &HBBGGRR&
                r = hex_color[0:2]
                g = hex_color[2:4]
                b = hex_color[4:6]
                return f"&H{b}{g}{r}&"
        
        # Default to yellow
        return color_map["yellow"]

