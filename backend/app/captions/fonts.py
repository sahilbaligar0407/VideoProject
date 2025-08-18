#!/usr/bin/env python3
"""
Font management for caption rendering.
Provides absolute paths to Poppins fonts with system fallbacks.
"""

import os
from pathlib import Path

def get_bundled_poppins_bold() -> str:
    """
    Get the path to Poppins-Bold.ttf font file.
    Returns an absolute, Windows-safe escaped path.
    """
    possible_paths = [
        "assets/fonts/poppins/Poppins-Bold.ttf",
        "outputs/Poppins-Bold.ttf",
        "Poppins-Bold.ttf",
        os.path.join(os.path.dirname(__file__), "..", "..", "assets", "fonts", "poppins", "Poppins-Bold.ttf"),
        os.path.join(os.path.dirname(__file__), "..", "..", "outputs", "Poppins-Bold.ttf")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            # Convert to absolute path and escape for Windows
            abs_path = os.path.abspath(path)
            # Escape backslashes and colons for FFmpeg on Windows
            escaped_path = abs_path.replace("\\", "\\\\").replace(":", "\\:")
            print(f"✅ Using Poppins Bold font: {abs_path}")
            return escaped_path
    
    # Fallback to system fonts if Poppins not found
    fallback_paths = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/tahoma.ttf"
    ]
    
    for path in fallback_paths:
        if os.path.exists(path):
            escaped_path = path.replace("\\", "\\\\").replace(":", "\\:")
            print(f"⚠️ Poppins Bold not found, using fallback: {path}")
            return escaped_path
    
    # Last resort
    print("⚠️ No suitable fonts found, using default")
    return "C:/Windows/Fonts/arial.ttf"

def get_bundled_poppins_black() -> str:
    """
    Get the path to Poppins-Black.ttf font file.
    Returns an absolute, Windows-safe escaped path.
    """
    possible_paths = [
        "assets/fonts/poppins/Poppins-Black.ttf",
        "outputs/Poppins-Black.ttf",
        "Poppins-Black.ttf",
        os.path.join(os.path.dirname(__file__), "..", "..", "assets", "fonts", "poppins", "Poppins-Black.ttf"),
        os.path.join(os.path.dirname(__file__), "..", "..", "outputs", "Poppins-Black.ttf")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            # Convert to absolute path and escape for Windows
            abs_path = os.path.abspath(path)
            # Escape backslashes and colons for FFmpeg on Windows
            escaped_path = abs_path.replace("\\", "\\\\").replace(":", "\\:")
            print(f"✅ Using Poppins Black font: {abs_path}")
            return escaped_path
    
    # Fallback to system fonts if Poppins not found
    fallback_paths = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/tahoma.ttf"
    ]
    
    for path in fallback_paths:
        if os.path.exists(path):
            escaped_path = path.replace("\\", "\\\\").replace(":", "\\:")
            print(f"⚠️ Poppins Black not found, using fallback: {path}")
            return escaped_path
    
    # Last resort
    print("⚠️ No suitable fonts found, using default")
    return "C:/Windows/Fonts/arial.ttf"

def get_bundled_poppins_extrabold() -> str:
    """
    Get the path to Poppins-ExtraBold.ttf font file.
    Returns an absolute, Windows-safe escaped path.
    """
    possible_paths = [
        "assets/fonts/poppins/Poppins-ExtraBold.ttf",
        "outputs/Poppins-ExtraBold.ttf",
        "Poppins-ExtraBold.ttf",
        os.path.join(os.path.dirname(__file__), "..", "..", "assets", "fonts", "poppins", "Poppins-ExtraBold.ttf"),
        os.path.join(os.path.dirname(__file__), "..", "..", "outputs", "Poppins-ExtraBold.ttf")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            # Convert to absolute path and escape for Windows
            abs_path = os.path.abspath(path)
            # Escape backslashes and colons for FFmpeg on Windows
            escaped_path = abs_path.replace("\\", "\\\\").replace(":", "\\:")
            print(f"✅ Using Poppins ExtraBold font: {abs_path}")
            return escaped_path
    
    # Fallback to system fonts if Poppins not found
    fallback_paths = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/tahoma.ttf"
    ]
    
    for path in fallback_paths:
        if os.path.exists(path):
            escaped_path = path.replace("\\", "\\\\").replace(":", "\\:")
            print(f"⚠️ Poppins ExtraBold not found, using fallback: {path}")
            return escaped_path
    
    # Last resort
    print("⚠️ No suitable fonts found, using default")
    return "C:/Windows/Fonts/arial.ttf"

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
