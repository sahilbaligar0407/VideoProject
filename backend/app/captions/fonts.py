#!/usr/bin/env python3
"""
Font management for caption rendering.
Provides absolute paths to Poppins fonts with system fallbacks.
"""

import os
from pathlib import Path

def get_bundled_poppins_bold() -> str:
    """
    Get the bundled Poppins-ExtraBold.ttf path with Windows-safe escaping.
    This is the primary font for caption rendering.
    """
    # Try multiple locations for the bundled Poppins font
    current_dir = Path(__file__).parent
    possible_paths = [
        # repo-relative: assets/fonts/poppins/Poppins-ExtraBold.ttf
        current_dir.parent.parent.parent / "assets" / "fonts" / "poppins" / "Poppins-ExtraBold.ttf",
        # outputs folder (where user placed it)
        current_dir.parent.parent.parent / "outputs" / "Poppins-ExtraBold.ttf",
        # current working directory
        Path.cwd() / "Poppins-ExtraBold.ttf",
        # outputs subdirectory
        Path.cwd() / "outputs" / "Poppins-ExtraBold.ttf"
    ]
    
    for poppins_path in possible_paths:
        if poppins_path.exists():
            # Convert to Windows-safe absolute path for FFmpeg
            abs_path = str(poppins_path.absolute())
            # Escape backslashes and colons for FFmpeg on Windows
            escaped_path = abs_path.replace("\\", "\\\\").replace(":", "\\:")
            print(f"✅ Using Poppins font: {abs_path}")
            return escaped_path
    
    # Fallback to system fonts if bundled font not found
    print("⚠️ Bundled Poppins font not found, falling back to system fonts")
    return get_fontfile("Poppins-ExtraBold.ttf")

def get_fontfile(preferred: str = "Poppins-ExtraBold.ttf") -> str:
    """
    Get absolute path to preferred font, with fallbacks to system fonts.
    
    Args:
        preferred: Preferred font filename (e.g., "Poppins-ExtraBold.ttf")
    
    Returns:
        Absolute path to available font file with Windows-safe escaping
    """
    # Try Poppins fonts in assets/fonts/poppins/
    current_dir = Path(__file__).parent
    poppins_dir = current_dir.parent.parent.parent / "assets" / "fonts" / "poppins"
    
    if poppins_dir.exists():
        poppins_font = poppins_dir / preferred
        if poppins_font.exists():
            # Convert to Windows-safe absolute path for FFmpeg
            abs_path = str(poppins_font.absolute())
            # Escape backslashes and colons for FFmpeg on Windows
            escaped_path = abs_path.replace("\\", "\\\\").replace(":", "\\:")
            return escaped_path
    
    # Try outputs folder (temporary location)
    outputs_dir = current_dir.parent.parent.parent / "outputs"
    if outputs_dir.exists():
        outputs_font = outputs_dir / preferred
        if outputs_font.exists():
            abs_path = str(outputs_font.absolute())
            escaped_path = abs_path.replace("\\", "\\\\").replace(":", "\\:")
            return escaped_path
    
    # Fallback to system fonts (Windows-safe paths)
    system_fonts = [
        "C\\:/Windows/Fonts/arial.ttf",
        "C\\:/Windows/Fonts/tahoma.ttf",
        "C\\:/Windows/Fonts/calibri.ttf"
    ]
    
    for font_path in system_fonts:
        if os.path.exists(font_path.replace("\\:", ":")):
            return font_path
    
    # Final fallback
    return "C\\:/Windows/Fonts/arial.ttf"

def get_poppins_bold() -> str:
    """Get Poppins-ExtraBold.ttf path with Windows-safe escaping"""
    return get_fontfile("Poppins-ExtraBold.ttf")

def get_poppins_regular() -> str:
    """Get Poppins-Regular.ttf path with Windows-safe escaping"""
    return get_fontfile("Poppins-Regular.ttf")

def get_poppins_medium() -> str:
    """Get Poppins-Medium.ttf path with Windows-safe escaping"""
    return get_fontfile("Poppins-Medium.ttf")
