"""
Test caption functionality for ClipGenius Pipeline v2.
Tests SRT, ASS, and VTT writers, and caption burning.
"""

import unittest
import os
import tempfile
import json
from unittest.mock import Mock, patch
import numpy as np

# Add the app directory to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.captions.styles import (
    CaptionStyle, CaptionTheme, generate_caption_styles,
    emphasize_keywords, wrap_caption_text, get_force_style_string,
    render_captions
)


class TestCaptionWriters(unittest.TestCase):
    """Test caption file writers"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_captions = [
            {"start": 0.0, "end": 2.0, "text": "Hello world"},
            {"start": 3.0, "end": 5.0, "text": "This is a test caption with some longer text"},
            {"start": 6.0, "end": 8.0, "text": "Short text"}
        ]
        
        self.style_config = generate_caption_styles(CaptionStyle.BOXED_HIGH_CONTRAST)
    
    def test_srt_writer_valid(self):
        """Test SRT writer creates valid format"""
        srt_content = render_captions(self.test_captions, self.style_config, "srt")
        
        # Check basic structure
        self.assertIn("1\n", srt_content)
        self.assertIn("2\n", srt_content)
        self.assertIn("3\n", srt_content)
        
        # Check timing format (HH:MM:SS,mmm)
        import re
        time_pattern = r'\d{2}:\d{2}:\d{2},\d{3}'
        times = re.findall(time_pattern, srt_content)
        self.assertEqual(len(times), 6)  # 3 start + 3 end times
        
        # Check cue separators (empty lines)
        self.assertIn("\n\n", srt_content)
        
        # Verify no literal "Dialogue:" strings
        self.assertNotIn("Dialogue:", srt_content)
    
    def test_srt_times_precision(self):
        """Test SRT time format has exactly 3 millisecond digits"""
        srt_content = render_captions(self.test_captions, self.style_config, "srt")
        
        # Check millisecond precision
        import re
        time_pattern = r'\d{2}:\d{2}:\d{2},(\d{3})'
        matches = re.findall(time_pattern, srt_content)
        
        for ms in matches:
            self.assertEqual(len(ms), 3, f"Millisecond precision should be 3 digits, got {len(ms)}")
    
    def test_srt_no_dialogue_literal(self):
        """Test SRT contains no literal 'Dialogue:' strings"""
        srt_content = render_captions(self.test_captions, self.style_config, "srt")
        
        # Should not contain ASS-style Dialogue: strings
        self.assertNotIn("Dialogue:", srt_content)
        
        # Should contain proper SRT format
        self.assertIn("1\n", srt_content)
        self.assertIn(" --> ", srt_content)
    
    def test_ass_writer_valid(self):
        """Test ASS writer creates valid format"""
        ass_content = render_captions(self.test_captions, self.style_config, "ass")
        
        # Check header
        self.assertIn("[Script Info]", ass_content)
        self.assertIn("[V4+ Styles]", ass_content)
        self.assertIn("[Events]", ass_content)
        self.assertIn("Style: Default", ass_content)
        
        # Check dialogue lines
        dialogue_count = ass_content.count("Dialogue:")
        self.assertEqual(dialogue_count, 3, f"Expected 3 dialogue lines, got {dialogue_count}")
        
        # Check each dialogue is on its own line
        lines = ass_content.split('\n')
        dialogue_lines = [line for line in lines if line.startswith('Dialogue:')]
        self.assertEqual(len(dialogue_lines), 3)
        
        # Check no commas in fields except Text
        for line in dialogue_lines:
            parts = line.split(',')
            self.assertGreaterEqual(len(parts), 10, "ASS dialogue should have at least 10 fields")
            
            # First 9 fields should not contain commas (except in Text field)
            for i in range(9):
                if i < len(parts):
                    self.assertNotIn(',', parts[i], f"Field {i} should not contain commas")
    
    def test_vtt_writer_valid(self):
        """Test VTT writer creates valid format"""
        vtt_content = render_captions(self.test_captions, self.style_config, "vtt")
        
        # Check header
        self.assertIn("WEBVTT", vtt_content)
        
        # Check cue blocks
        cue_blocks = vtt_content.split('\n\n')
        self.assertEqual(len(cue_blocks), 4)  # Header + 3 cues
        
        # Check first cue contains only first caption
        first_cue = cue_blocks[1]
        self.assertIn("1", first_cue)
        self.assertIn("Hello world", first_cue)
        self.assertNotIn("This is a test", first_cue)  # Should not contain second caption
        
        # Check timing format (HH:MM:SS.mmm)
        import re
        time_pattern = r'\d{2}:\d{2}:\d{2}\.\d{3}'
        times = re.findall(time_pattern, vtt_content)
        self.assertEqual(len(times), 6)  # 3 start + 3 end times
        
        # Verify no literal "Dialogue:" strings
        self.assertNotIn("Dialogue:", vtt_content)
    
    def test_caption_wrapping(self):
        """Test caption text wrapping"""
        long_text = "This is a very long caption text that should be wrapped to multiple lines to fit within the specified character limits"
        
        # Test wrapping to 2 lines max, 35 chars per line
        wrapped = wrap_caption_text(long_text, max_width_chars=35, max_lines=2)
        lines = wrapped.split("\\N")
        
        self.assertLessEqual(len(lines), 2, "Should wrap to max 2 lines")
        for line in lines:
            self.assertLessEqual(len(line), 35, f"Line should be <= 35 chars: '{line}'")
    
    def test_keyword_emphasis(self):
        """Test keyword emphasis in captions"""
        text = "This is a test message with important keywords"
        keywords = ["test", "important", "keywords"]
        
        # Test bold emphasis
        bold_text = emphasize_keywords(text, keywords, "bold")
        self.assertIn("\b1test\b0", bold_text)
        self.assertIn("\b1important\b0", bold_text)
        self.assertIn("\b1keywords\b0", bold_text)
        
        # Test caps emphasis
        caps_text = emphasize_keywords(text, keywords, "caps")
        self.assertIn("TEST", caps_text)
        self.assertIn("IMPORTANT", caps_text)
        self.assertIn("KEYWORDS", caps_text)


class TestForceStyleGeneration(unittest.TestCase):
    """Test FFmpeg force_style string generation"""
    
    def test_boxed_high_contrast_style(self):
        """Test boxed high contrast style generation"""
        style_config = generate_caption_styles(CaptionStyle.BOXED_HIGH_CONTRAST)
        force_style = get_force_style_string(style_config)
        
        # Should contain key style parameters
        self.assertIn("Fontname=Inter", force_style)
        self.assertIn("Fontsize=48", force_style)
        self.assertIn("BorderStyle=3", force_style)  # Boxed
        self.assertIn("Outline=4", force_style)
        self.assertIn("Alignment=2", force_style)  # Bottom-center
        self.assertIn("MarginV=160", force_style)
    
    def test_outline_bold_style(self):
        """Test outline bold style generation"""
        style_config = generate_caption_styles(CaptionStyle.OUTLINE_BOLD)
        force_style = get_force_style_string(style_config)
        
        # Should contain outline-specific parameters
        self.assertIn("Fontsize=48", force_style)
        self.assertIn("Outline=5", force_style)
        self.assertIn("BorderStyle=1", force_style)  # Outline
        self.assertIn("Alignment=2", force_style)
        self.assertIn("MarginV=160", force_style)


if __name__ == "__main__":
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_suite.addTest(unittest.makeSuite(TestCaptionWriters))
    test_suite.addTest(unittest.makeSuite(TestForceStyleGeneration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
