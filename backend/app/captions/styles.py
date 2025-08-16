"""
Production-quality caption styling for ClipGenius Pipeline v2.
Provides clean, bold styles with boxed/outline presets and keyword emphasis.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import re

class CaptionStyle(str, Enum):
    """Caption style presets"""
    BOXED_HIGH_CONTRAST = "boxed_high_contrast"  # Default: high contrast boxed style
    OUTLINE_BOLD = "outline_bold"                 # Bold outline style
    KARAOKE = "karaoke"                          # Karaoke style with word timing
    MODERN = "modern"                             # Clean modern style
    CLASSIC = "classic"                           # Classic subtitle style

class CaptionTheme(str, Enum):
    """Caption theme presets"""
    DEFAULT = "default"                           # Default theme
    MODERN = "modern"                             # Modern clean theme
    BOLD = "bold"                                 # Bold high-contrast theme
    SUBTLE = "subtle"                             # Subtle professional theme

def generate_caption_styles(
    style: CaptionStyle = CaptionStyle.BOXED_HIGH_CONTRAST,
    theme: CaptionTheme = CaptionTheme.DEFAULT,
    custom_colors: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Generate caption style configuration for the specified style and theme.
    
    Args:
        style: Caption style preset
        theme: Caption theme preset
        custom_colors: Optional custom color overrides
        
    Returns:
        Style configuration dictionary
    """
    # Base style configurations
    base_styles = {
        CaptionStyle.BOXED_HIGH_CONTRAST: {
            "fontname": "Inter",
            "fontsize": 48,
            "border_style": 3,  # Boxed
            "outline": 4,
            "outline_colour": "&H99000000&",  # Semi-transparent black
            "primary_colour": "&H00FFFFFF&",   # White
            "alignment": 2,  # Bottom-center
            "margin_v": 160,
            "bold": 1,
            "shadow": 0,
            "max_width_chars": 38,
            "line_height": 1.2
        },
        CaptionStyle.OUTLINE_BOLD: {
            "fontname": "Inter",
            "fontsize": 48,
            "border_style": 1,  # Outline
            "outline": 5,
            "outline_colour": "&HCC000000&",  # More opaque black
            "primary_colour": "&H00FFFFFE&",   # Bright white
            "alignment": 2,  # Bottom-center
            "margin_v": 160,
            "bold": 1,
            "shadow": 0,
            "max_width_chars": 38,
            "line_height": 1.2
        },
        CaptionStyle.KARAOKE: {
            "fontname": "Inter",
            "fontsize": 44,
            "border_style": 3,  # Boxed
            "outline": 3,
            "outline_colour": "&H66000000&",  # Semi-transparent black
            "primary_colour": "&H00FFFFFF&",   # White
            "alignment": 2,  # Bottom-center
            "margin_v": 160,
            "bold": 1,
            "shadow": 1,
            "max_width_chars": 36,
            "line_height": 1.3
        },
        CaptionStyle.MODERN: {
            "fontname": "Inter",
            "fontsize": 42,
            "border_style": 1,  # Outline
            "outline": 3,
            "outline_colour": "&H80000000&",  # Semi-transparent black
            "primary_colour": "&H00FFFFFF&",   # White
            "alignment": 2,  # Bottom-center
            "margin_v": 160,
            "bold": 0,
            "shadow": 1,
            "max_width_chars": 40,
            "line_height": 1.1
        },
        CaptionStyle.CLASSIC: {
            "fontname": "Arial",
            "fontsize": 40,
            "border_style": 1,  # Outline
            "outline": 2,
            "outline_colour": "&H00000000&",  # Black
            "primary_colour": "&H00FFFFFF&",   # White
            "alignment": 2,  # Bottom-center
            "margin_v": 160,
            "bold": 0,
            "shadow": 0,
            "max_width_chars": 42,
            "line_height": 1.0
        }
    }
    
    # Theme-based color adjustments
    theme_colors = {
        CaptionTheme.DEFAULT: {},
        CaptionTheme.MODERN: {
            "primary_colour": "&H00F0F0F0&",   # Light gray
            "outline_colour": "&H99000000&"     # Semi-transparent black
        },
        CaptionTheme.BOLD: {
            "primary_colour": "&H00FFFFFF&",    # Bright white
            "outline_colour": "&HCC000000&",    # More opaque black
            "bold": 1
        },
        CaptionTheme.SUBTLE: {
            "primary_colour": "&H00E0E0E0&",   # Subtle white
            "outline_colour": "&H66000000&",    # More transparent black
            "bold": 0
        }
    }
    
    # Start with base style
    style_config = base_styles[style].copy()
    
    # Apply theme colors
    theme_config = theme_colors[theme]
    style_config.update(theme_config)
    
    # Apply custom color overrides
    if custom_colors:
        style_config.update(custom_colors)
    
    return style_config

def emphasize_keywords(text: str, keywords: List[str], emphasis_style: str = "bold") -> str:
    """
    Emphasize keywords in caption text.
    
    Args:
        text: Original caption text
        keywords: List of keywords to emphasize
        emphasis_style: "bold", "caps", or "highlight"
        
    Returns:
        Text with emphasized keywords
    """
    if not keywords:
        return text
    
    # Sort keywords by length (longest first) to avoid partial matches
    sorted_keywords = sorted(keywords, key=len, reverse=True)
    
    emphasized_text = text
    
    for keyword in sorted_keywords:
        if keyword.lower() in emphasized_text.lower():
            # Find the actual case in the text
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            
            if emphasis_style == "bold":
                replacement = f"\\b1{keyword}\\b0"
            elif emphasis_style == "caps":
                replacement = keyword.upper()
            elif emphasis_style == "highlight":
                replacement = f"\\3c&H00FFFF00&{keyword}\\3c&H00FFFFFF&"
            else:
                replacement = keyword
            
            emphasized_text = pattern.sub(replacement, emphasized_text)
    
    return emphasized_text

def wrap_caption_text(text: str, max_width_chars: int = 38, max_lines: int = 2) -> str:
    """
    Wrap caption text to fit within specified constraints.
    
    Args:
        text: Original caption text
        max_width_chars: Maximum characters per line
        max_lines: Maximum number of lines
        
    Returns:
        Wrapped text with line breaks
    """
    if len(text) <= max_width_chars:
        return text
    
    # Split into words
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        # Check if adding this word would exceed line length
        if len(current_line) + len(word) + 1 <= max_width_chars:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
        else:
            # Start new line
            if current_line:
                lines.append(current_line)
                current_line = word
            else:
                # Word is too long for one line, split it
                if len(word) > max_width_chars:
                    # Split long word
                    while len(word) > max_width_chars:
                        lines.append(word[:max_width_chars])
                        word = word[max_width_chars:]
                    if word:
                        current_line = word
                else:
                    current_line = word
    
    # Add the last line
    if current_line:
        lines.append(current_line)
    
    # Limit to max_lines
    if len(lines) > max_lines:
        # Truncate and add ellipsis
        lines = lines[:max_lines]
        if len(lines) == max_lines:
            # Truncate last line if needed
            last_line = lines[-1]
            if len(last_line) > max_width_chars - 3:
                lines[-1] = last_line[:max_width_chars - 3] + "..."
    
    return "\\N".join(lines)

def render_captions(
    captions: List[Dict[str, Any]],
    style_config: Dict[str, Any],
    output_format: str = "ass",
    keywords: Optional[List[str]] = None,
    emphasis_style: str = "bold"
) -> str:
    """
    Render captions in the specified format with styling.
    
    Args:
        captions: List of caption dictionaries with start, end, text
        style_config: Caption style configuration
        output_format: Output format ("ass", "vtt", "srt")
        keywords: Optional keywords for emphasis
        emphasis_style: Style for keyword emphasis
        
    Returns:
        Rendered captions as string
    """
    if output_format == "ass":
        return _render_ass_captions(captions, style_config, keywords, emphasis_style)
    elif output_format == "vtt":
        return _render_vtt_captions(captions, style_config, keywords, emphasis_style)
    elif output_format == "srt":
        return _render_srt_captions(captions, style_config, keywords, emphasis_style)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")

def _render_ass_captions(
    captions: List[Dict[str, Any]], 
    style_config: Dict[str, Any],
    keywords: Optional[List[str]] = None,
    emphasis_style: str = "bold"
) -> str:
    """Render captions in ASS format with advanced styling"""
    
    # ASS header
    ass_content = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "WrapStyle: 2",  # Smart wrapping
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,{style_config['fontname']},{style_config['fontsize']},{style_config['primary_colour']},{style_config['primary_colour']},{style_config['outline_colour']},&H00000000&,{style_config['bold']},0,0,0,100,100,0,0,{style_config['border_style']},{style_config['outline']},{style_config['shadow']},{style_config['alignment']},80,80,{style_config['margin_v']},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]
    
    # Process each caption
    for i, caption in enumerate(captions):
        start_time = caption.get('start', 0)
        end_time = caption.get('end', 0)
        text = caption.get('text', '')
        
        # Emphasize keywords if provided
        if keywords:
            text = emphasize_keywords(text, keywords, emphasis_style)
        
        # Wrap text
        wrapped_text = wrap_caption_text(
            text, 
            style_config.get('max_width_chars', 38),
            style_config.get('max_lines', 2)
        )
        
        # Format times for ASS
        start_ass = _format_ass_time(start_time)
        end_ass = _format_ass_time(end_time)
        
        # Escape ASS special characters
        escaped_text = wrapped_text.replace(",", "\\,").replace("\\N", "\\N")
        
        # Add caption line
        ass_content.append(
            f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{escaped_text}"
        )
    
    return "\n".join(ass_content)

def _render_vtt_captions(
    captions: List[Dict[str, Any]], 
    style_config: Dict[str, Any],
    keywords: Optional[List[str]] = None,
    emphasis_style: str = "bold"
) -> str:
    """Render captions in WebVTT format"""
    
    vtt_content = ["WEBVTT", ""]
    
    for i, caption in enumerate(captions):
        start_time = caption.get('start', 0)
        end_time = caption.get('end', 0)
        text = caption.get('text', '')
        
        # Emphasize keywords if provided
        if keywords:
            text = emphasize_keywords(text, keywords, emphasis_style)
        
        # Wrap text
        wrapped_text = wrap_caption_text(
            text, 
            style_config.get('max_width_chars', 38),
            style_config.get('max_lines', 2)
        )
        
        # Format times for VTT
        start_vtt = _format_vtt_time(start_time)
        end_vtt = _format_vtt_time(end_time)
        
        # Add caption
        vtt_content.extend([
            str(i + 1),
            f"{start_vtt} --> {end_vtt}",
            wrapped_text,
            ""
        ])
    
    return "\n".join(vtt_content)

def _render_srt_captions(
    captions: List[Dict[str, Any]], 
    style_config: Dict[str, Any],
    keywords: Optional[List[str]] = None,
    emphasis_style: str = "bold"
) -> str:
    """Render captions in SRT format"""
    
    srt_content = []
    
    for i, caption in enumerate(captions):
        start_time = caption.get('start', 0)
        end_time = caption.get('end', 0)
        text = caption.get('text', '')
        
        # Emphasize keywords if provided
        if keywords:
            text = emphasize_keywords(text, keywords, emphasis_style)
        
        # Wrap text
        wrapped_text = wrap_caption_text(
            text, 
            style_config.get('max_width_chars', 38),
            style_config.get('max_lines', 2)
        )
        
        # Format times for SRT
        start_srt = _format_srt_time(start_time)
        end_srt = _format_srt_time(end_time)
        
        # Add caption
        srt_content.extend([
            str(i + 1),
            f"{start_srt} --> {end_srt}",
            wrapped_text,
            ""
        ])
    
    return "\n".join(srt_content)

def _hex_to_ass_color(hex_color: str) -> str:
    """Convert hex color to ASS color format"""
    # Remove # if present
    hex_color = hex_color.lstrip('#')
    
    # Convert to RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # ASS uses BGR format with alpha
    return f"&H00{b:02x}{g:02x}{r:02x}&"

def _format_ass_time(seconds: float) -> str:
    """Format time for ASS format (H:MM:SS.cc)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centisecs = int((seconds % 1) * 100)
    
    return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

def _format_vtt_time(seconds: float) -> str:
    """Format time for VTT format (HH:MM:SS.mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"

def _format_srt_time(seconds: float) -> str:
    """Format time for SRT format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def get_force_style_string(style_config: Dict[str, Any]) -> str:
    """
    Generate FFmpeg force_style string for SRT burn-in.
    
    Args:
        style_config: Caption style configuration
        
    Returns:
        FFmpeg force_style string
    """
    style_parts = []
    
    # Map style config to FFmpeg force_style parameters
    mappings = {
        'fontname': 'Fontname',
        'fontsize': 'Fontsize',
        'border_style': 'BorderStyle',
        'outline': 'Outline',
        'outline_colour': 'OutlineColour',
        'primary_colour': 'PrimaryColour',
        'alignment': 'Alignment',
        'margin_v': 'MarginV',
        'bold': 'Bold',
        'shadow': 'Shadow'
    }
    
    for config_key, ffmpeg_key in mappings.items():
        if config_key in style_config:
            value = style_config[config_key]
            
            # Handle special cases
            if config_key == 'outline_colour' and isinstance(value, str) and value.startswith('&H'):
                # Convert ASS color to hex for FFmpeg
                value = _ass_color_to_hex(value)
            elif config_key == 'bold':
                value = '1' if value else '0'
            
            style_parts.append(f"{ffmpeg_key}={value}")
    
    return ','.join(style_parts)

def _ass_color_to_hex(ass_color: str) -> str:
    """Convert ASS color format to hex"""
    # ASS format: &HAABBGGRR&
    # Extract BGR values
    match = re.search(r'&H([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})&', ass_color)
    if match:
        b, g, r = match.groups()
        return f"#{r}{g}{b}"
    return "#FFFFFF"  # Default to white
