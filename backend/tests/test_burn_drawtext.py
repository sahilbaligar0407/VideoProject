#!/usr/bin/env python3
"""
Unit tests for the bulletproof drawtext filter builder.
"""

import unittest
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from captions.burn_drawtext import (
    build_drawtext_filter,
    validate_filter_string,
    wrap_caption_text,
    escape_text_for_drawtext,
    get_font_path,
    get_style_config
)


class TestBurnDrawtext(unittest.TestCase):
    """Test the bulletproof drawtext filter builder"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_segments = [
            {
                'start': 0.0,
                'end': 2.0,
                'text': 'Hello world'
            },
            {
                'start': 2.0,
                'end': 4.0,
                'text': 'This is a longer caption that should wrap to two lines'
            },
            {
                'start': 4.0,
                'end': 6.0,
                'text': 'Short text'
            }
        ]
    
    def test_build_drawtext_filter(self):
        """Test building a complete drawtext filter chain"""
        filter_string = build_drawtext_filter(
            clip_start=0.0,
            segments=self.test_segments,
            style="boxed_high_contrast"
        )
        
        # Should contain exactly 3 drawtext filters
        self.assertEqual(filter_string.count('drawtext='), 3)
        
        # Should contain proper chaining (commas between filters)
        comma_count = filter_string.count(',')
        self.assertGreaterEqual(comma_count, 2)  # At least 2 commas for 3 filters
        
        # Should contain enable='between(t,...)' patterns
        self.assertIn("enable='between(t,0.00,2.00)'", filter_string)
        self.assertIn("enable='between(t,2.00,4.00)'", filter_string)
        self.assertIn("enable='between(t,4.00,6.00)'", filter_string)
    
    def test_validate_filter_string(self):
        """Test filter string validation"""
        # Valid filter string
        valid_filter = "drawtext=text='Hello':enable='between(t,0.0,2.0)',drawtext=text='World':enable='between(t,2.0,4.0)'"
        self.assertTrue(validate_filter_string(valid_filter))
        
        # Invalid: negative start time
        invalid_filter = "drawtext=text='Hello':enable='between(t,-1.0,2.0)'"
        self.assertFalse(validate_filter_string(invalid_filter))
        
        # Invalid: start >= end
        invalid_filter = "drawtext=text='Hello':enable='between(t,2.0,1.0)'"
        self.assertFalse(validate_filter_string(invalid_filter))
    
    def test_wrap_caption_text(self):
        """Test text wrapping logic"""
        # Short text should not wrap
        short_text = "Hello world"
        wrapped = wrap_caption_text(short_text, 38)
        self.assertEqual(wrapped, "Hello world")
        
        # Long text should wrap to 2 lines
        long_text = "This is a very long caption that should definitely wrap to two lines because it exceeds the character limit"
        wrapped = wrap_caption_text(long_text, 38)
        
        # Should contain \N for newline
        self.assertIn("\\N", wrapped)
        
        # Should be split into 2 parts
        parts = wrapped.split("\\N")
        self.assertEqual(len(parts), 2)
        
        # Each line should be within character limit
        self.assertLessEqual(len(parts[0]), 38)
        self.assertLessEqual(len(parts[1]), 38)
    
    def test_escape_text_for_drawtext(self):
        """Test text escaping for drawtext"""
        # Test single quote escaping
        text_with_quotes = "Don't say \"hello\""
        escaped = escape_text_for_drawtext(text_with_quotes)
        
        self.assertIn("\\'", escaped)  # Single quote escaped
        self.assertIn('\\"', escaped)  # Double quote escaped
        
        # Test newline preservation
        text_with_newline = "Line 1\nLine 2"
        escaped = escape_text_for_drawtext(text_with_newline)
        self.assertIn("\\N", escaped)  # \n converted to \N
    
    def test_get_style_config(self):
        """Test style configuration retrieval"""
        # Test default style
        default_style = get_style_config("boxed_high_contrast")
        self.assertEqual(default_style["fontsize"], 48)
        self.assertEqual(default_style["box"], 1)
        self.assertEqual(default_style["max_chars_per_line"], 38)
        
        # Test outline style
        outline_style = get_style_config("outline_bold")
        self.assertEqual(outline_style["fontsize"], 48)
        self.assertEqual(outline_style["box"], 0)
        self.assertEqual(outline_style["max_chars_per_line"], 36)
        
        # Test unknown style (should return default)
        unknown_style = get_style_config("unknown_style")
        self.assertEqual(unknown_style["fontsize"], 48)  # Default values
    
    def test_clip_relative_timing(self):
        """Test that times are converted to clip-relative"""
        filter_string = build_drawtext_filter(
            clip_start=10.0,  # Clip starts at 10 seconds
            segments=[
                {'start': 10.0, 'end': 12.0, 'text': 'Hello'},  # Should become 0.0-2.0
                {'start': 12.0, 'end': 14.0, 'text': 'World'}   # Should become 2.0-4.0
            ]
        )
        
        # Times should be clip-relative (0.0, 2.0, etc.)
        self.assertIn("enable='between(t,0.00,2.00)'", filter_string)
        self.assertIn("enable='between(t,2.00,4.00)'", filter_string)
        
        # Should not contain original times
        self.assertNotIn("enable='between(t,10.00,12.00)'", filter_string)
        self.assertNotIn("enable='between(t,12.00,14.00)'", filter_string)
    
    def test_safe_positioning(self):
        """Test that Y positioning is safe (never negative)"""
        filter_string = build_drawtext_filter(
            clip_start=0.0,
            segments=self.test_segments
        )
        
        # Should contain safe Y positioning
        self.assertIn("y='if(gt(h-160-text_h,0),h-160-text_h,10)'", filter_string)
        
        # Should not contain unsafe positioning
        self.assertNotIn("y=h-160-text_h", filter_string)


if __name__ == "__main__":
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_suite.addTest(unittest.makeSuite(TestBurnDrawtext))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
