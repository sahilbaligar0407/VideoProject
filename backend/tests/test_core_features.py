"""
Comprehensive test suite for ClipGenius Pipeline v2 core features.
Tests dynamic layout switching, caption styling, and multi-language support.
"""

import unittest
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import cv2

# Add the app directory to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.layout.state_machine import LayoutStateMachine, LayoutState, FaceTrack
from app.captions.styles import (
    CaptionStyle, CaptionTheme, generate_caption_styles,
    emphasize_keywords, wrap_caption_text, get_force_style_string
)
from app.captions.translate import (
    get_supported_languages, detect_caption_language,
    validate_translation_quality
)
from app.output.manifest import generate_clip_manifest


class TestLayoutStateMachine(unittest.TestCase):
    """Test the dynamic layout state machine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.state_machine = LayoutStateMachine(
            face_confidence_threshold=0.7,
            state_debounce_frames=3,  # Lower for testing
            min_face_size=50,
            scene_cut_threshold=0.3
        )
        
        # Create mock frame
        self.mock_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        
        # Create mock speech segments
        self.speech_segments = [
            {"start": 0.0, "end": 2.0, "text": "Hello world"},
            {"start": 3.0, "end": 5.0, "text": "How are you"}
        ]
        self.state_machine.update_speech_segments(self.speech_segments)
    
    def test_initial_state(self):
        """Test initial state is BG_BLUR_RECT"""
        self.assertEqual(self.state_machine.current_state, LayoutState.BG_BLUR_RECT)
        self.assertEqual(self.state_machine.face_detection_count, 0)
        self.assertEqual(self.state_machine.no_face_count, 0)
    
    def test_face_detection(self):
        """Test face detection and tracking"""
        # Mock MediaPipe face detection
        with patch.object(self.state_machine.mp_face_detection, 'process') as mock_process:
            # Create mock detection result
            mock_detection = Mock()
            mock_detection.score = [0.9]  # High confidence
            mock_detection.location_data.relative_bounding_box.xmin = 0.4
            mock_detection.location_data.relative_bounding_box.ymin = 0.3
            mock_detection.location_data.relative_bounding_box.width = 0.2
            mock_detection.location_data.relative_bounding_box.height = 0.3
            
            mock_results = Mock()
            mock_results.detections = [mock_detection]
            mock_process.return_value = mock_results
            
            # Test face detection
            detected_faces = self.state_machine.detect_faces(self.mock_frame, 0)
            
            self.assertEqual(len(detected_faces), 1)
            self.assertEqual(detected_faces[0].confidence, 0.9)
            self.assertEqual(detected_faces[0].track_id, 0)
    
    def test_state_transition_to_vert_focus(self):
        """Test transition to VERT_FOCUS when face detected"""
        # Mock face detection for multiple frames
        with patch.object(self.state_machine, 'detect_faces') as mock_detect:
            mock_face = FaceTrack(
                track_id=0,
                bbox=(400, 300, 200, 300),
                confidence=0.9,
                speaking_score=0.8
            )
            mock_detect.return_value = [mock_face]
            
            # Update state for multiple frames to trigger transition
            for frame in range(5):
                state = self.state_machine.update_state(self.mock_frame, frame)
            
            # Should transition to VERT_FOCUS after debounce frames
            self.assertEqual(self.state_machine.current_state, LayoutState.VERT_FOCUS)
            self.assertEqual(len(self.state_machine.state_history), 1)
    
    def test_scene_cut_detection(self):
        """Test scene cut detection"""
        # Create two different frames
        frame1 = np.zeros((1080, 1920, 3), dtype=np.uint8)
        frame2 = np.ones((1080, 1920, 3), dtype=np.uint8) * 255
        
        # First frame should not detect scene cut
        scene_cut1 = self.state_machine.detect_scene_cut(frame1, 0)
        self.assertFalse(scene_cut1)
        
        # Second frame should detect scene cut (very different)
        scene_cut2 = self.state_machine.detect_scene_cut(frame2, 1)
        self.assertTrue(scene_cut2)
    
    def test_primary_face_selection(self):
        """Test primary face selection based on speaking score"""
        faces = [
            FaceTrack(track_id=0, bbox=(100, 100, 200, 200), confidence=0.8, speaking_score=0.3),
            FaceTrack(track_id=1, bbox=(300, 300, 200, 200), confidence=0.9, speaking_score=0.9),
            FaceTrack(track_id=2, bbox=(500, 500, 200, 200), confidence=0.7, speaking_score=0.5)
        ]
        
        primary_face = self.state_machine.select_primary_face(faces)
        self.assertEqual(primary_face.track_id, 1)  # Highest speaking score
        self.assertEqual(primary_face.speaking_score, 0.9)
    
    def test_speaking_score_computation(self):
        """Test speaking score computation"""
        bbox = (400, 300, 200, 300)
        frame_time = 1.5  # Should overlap with first speech segment
        
        score = self.state_machine.compute_speaking_score(bbox, frame_time)
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)
    
    def test_get_current_layout_config(self):
        """Test getting current layout configuration"""
        config = self.state_machine.get_current_layout_config()
        
        self.assertIn("state", config)
        self.assertIn("primary_face", config)
        self.assertIn("scene_cut_detected", config)
        self.assertEqual(config["state"], "bg_blur_rect")
    
    def test_get_state_timeline(self):
        """Test getting state timeline"""
        timeline = self.state_machine.get_state_timeline()
        
        self.assertEqual(len(timeline), 1)  # Initial state
        self.assertEqual(timeline[0]["state"], "bg_blur_rect")
        self.assertIsNone(timeline[0]["frame_end"])


class TestCaptionStyles(unittest.TestCase):
    """Test caption styling and formatting"""
    
    def test_generate_caption_styles(self):
        """Test caption style generation"""
        # Test default style
        default_style = generate_caption_styles()
        self.assertEqual(default_style["fontname"], "Inter")
        self.assertEqual(default_style["fontsize"], 48)
        self.assertEqual(default_style["border_style"], 3)  # Boxed
        self.assertEqual(default_style["alignment"], 2)  # Bottom-center
        
        # Test outline bold style
        outline_style = generate_caption_styles(CaptionStyle.OUTLINE_BOLD)
        self.assertEqual(outline_style["border_style"], 1)  # Outline
        self.assertEqual(outline_style["outline"], 5)
        self.assertEqual(outline_style["bold"], 1)
        
        # Test custom colors
        custom_style = generate_caption_styles(
            CaptionStyle.BOXED_HIGH_CONTRAST,
            CaptionTheme.BOLD,
            {"primary_colour": "&H00FF0000&"}  # Red
        )
        self.assertEqual(custom_style["primary_colour"], "&H00FF0000&")
    
    def test_emphasize_keywords(self):
        """Test keyword emphasis"""
        text = "This is a test message with important keywords"
        keywords = ["test", "important", "keywords"]
        
        # Test bold emphasis
        bold_text = emphasize_keywords(text, keywords, "bold")
        self.assertIn("\\b1test\\b0", bold_text)
        self.assertIn("\\b1important\\b0", bold_text)
        self.assertIn("\\b1keywords\\b0", bold_text)
        
        # Test caps emphasis
        caps_text = emphasize_keywords(text, keywords, "caps")
        self.assertIn("TEST", caps_text)
        self.assertIn("IMPORTANT", caps_text)
        self.assertIn("KEYWORDS", caps_text)
    
    def test_wrap_caption_text(self):
        """Test caption text wrapping"""
        long_text = "This is a very long caption text that should be wrapped to multiple lines to fit within the specified character limits"
        
        # Test wrapping
        wrapped = wrap_caption_text(long_text, max_width_chars=30, max_lines=2)
        lines = wrapped.split("\\N")
        
        self.assertLessEqual(len(lines), 2)
        for line in lines:
            self.assertLessEqual(len(line), 30)
        
        # Test short text (no wrapping needed)
        short_text = "Short caption"
        wrapped_short = wrap_caption_text(short_text, max_width_chars=30)
        self.assertEqual(wrapped_short, short_text)
    
    def test_get_force_style_string(self):
        """Test FFmpeg force_style string generation"""
        style_config = generate_caption_styles(CaptionStyle.BOXED_HIGH_CONTRAST)
        force_style = get_force_style_string(style_config)
        
        # Should contain key style parameters
        self.assertIn("Fontname=Inter", force_style)
        self.assertIn("Fontsize=48", force_style)
        self.assertIn("BorderStyle=3", force_style)
        self.assertIn("Alignment=2", force_style)


class TestCaptionTranslation(unittest.TestCase):
    """Test caption translation functionality"""
    
    def test_supported_languages(self):
        """Test supported languages list"""
        languages = get_supported_languages()
        
        # Should have common languages
        language_codes = [lang["code"] for lang in languages]
        self.assertIn("en", language_codes)
        self.assertIn("es", language_codes)
        self.assertIn("fr", language_codes)
        self.assertIn("de", language_codes)
        self.assertIn("ja", language_codes)
        self.assertIn("zh", language_codes)
        
        # Each language should have required fields
        for lang in languages:
            self.assertIn("code", lang)
            self.assertIn("name", lang)
            self.assertIn("native", lang)
    
    def test_translation_quality_validation(self):
        """Test translation quality validation"""
        original_captions = [
            {"start": 0.0, "end": 2.0, "text": "Hello world"},
            {"start": 3.0, "end": 5.0, "text": "How are you"}
        ]
        
        # Perfect translation
        perfect_translation = [
            {"start": 0.0, "end": 2.0, "text": "Hola mundo"},
            {"start": 3.0, "end": 5.0, "text": "¿Cómo estás?"}
        ]
        
        quality = validate_translation_quality(original_captions, perfect_translation, "es")
        self.assertTrue(quality["valid"])
        self.assertEqual(quality["quality_level"], "excellent")
        
        # Translation with timestamp errors
        bad_translation = [
            {"start": 1.0, "end": 2.0, "text": "Hola mundo"},  # Wrong start time
            {"start": 3.0, "end": 5.0, "text": "¿Cómo estás?"}
        ]
        
        quality_bad = validate_translation_quality(original_captions, bad_translation, "es")
        self.assertFalse(quality_bad["valid"])
        self.assertIn("start time mismatch", quality_bad["timestamp_errors"][0])


class TestManifestGeneration(unittest.TestCase):
    """Test manifest generation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.clip_id = "test_clip_123"
        self.source_video = "/path/to/source.mp4"
        self.output_path = os.path.join(self.temp_dir, "test_output.mp4")
        
        # Create dummy output file
        with open(self.output_path, 'w') as f:
            f.write("dummy content")
        
        self.layout_states = [
            {
                "frame": 0,
                "state": "bg_blur_rect",
                "config": {"primary_face": None, "scene_cut_detected": False}
            },
            {
                "frame": 30,
                "state": "vert_focus",
                "config": {
                    "primary_face": {
                        "track_id": 0,
                        "bbox": [400, 300, 200, 300],
                        "speaking_score": 0.8
                    },
                    "scene_cut_detected": False
                }
            }
        ]
        
        self.caption_info = {
            "enabled": True,
            "mode": "burn",
            "style": "boxed_high_contrast",
            "theme": "default",
            "languages": ["en", "es"],
            "burn_in_language": "en"
        }
        
        self.processing_metadata = {
            "processing_time": 15.5,
            "highlight_detection": {"score": 0.85},
            "viral_scoring": {"viral_score": 0.72}
        }
    
    def test_generate_clip_manifest(self):
        """Test clip manifest generation"""
        manifest_path = generate_clip_manifest(
            self.clip_id,
            self.source_video,
            10.0,  # start_time
            25.0,  # end_time
            15.0,  # duration
            self.output_path,
            self.layout_states,
            self.caption_info,
            self.processing_metadata,
            self.temp_dir
        )
        
        self.assertTrue(os.path.exists(manifest_path))
        
        # Load and validate manifest
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Check required fields
        self.assertEqual(manifest["clip_id"], self.clip_id)
        self.assertEqual(manifest["version"], "2.0.0")
        self.assertEqual(manifest["source"]["duration"], 15.0)
        self.assertEqual(manifest["output"]["resolution"], "1080x1920")
        self.assertEqual(manifest["layout"]["mode"], "dynamic")
        self.assertEqual(manifest["captions"]["enabled"], True)
        self.assertEqual(manifest["captions"]["languages"], ["en", "es"])
        
        # Check layout states
        self.assertEqual(len(manifest["layout"]["states"]), 2)
        self.assertEqual(manifest["layout"]["states"][0]["state"], "bg_blur_rect")
        self.assertEqual(manifest["layout"]["states"][1]["state"], "vert_focus")
        
        # Check quality assessment
        self.assertIn("quality", manifest)
        self.assertIn("overall_score", manifest["quality"])
        self.assertIn("layout_score", manifest["quality"])
        self.assertIn("caption_score", manifest["quality"])
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)


class TestIntegration(unittest.TestCase):
    """Integration tests for core features"""
    
    def test_end_to_end_layout_processing(self):
        """Test end-to-end layout processing workflow"""
        # Create state machine
        state_machine = LayoutStateMachine(
            face_confidence_threshold=0.7,
            state_debounce_frames=2,  # Low for testing
            min_face_size=50
        )
        
        # Mock speech segments
        speech_segments = [{"start": 0.0, "end": 5.0, "text": "Test speech"}]
        state_machine.update_speech_segments(speech_segments)
        
        # Process frames
        frame_states = []
        for frame_num in range(10):
            # Create mock frame (alternating between face/no-face)
            if frame_num % 2 == 0:
                # Frame with face
                with patch.object(state_machine, 'detect_faces') as mock_detect:
                    mock_face = FaceTrack(
                        track_id=0,
                        bbox=(400, 300, 200, 300),
                        confidence=0.9,
                        speaking_score=0.8
                    )
                    mock_detect.return_value = [mock_face]
                    state = state_machine.update_state(np.zeros((1080, 1920, 3)), frame_num)
            else:
                # Frame without face
                with patch.object(state_machine, 'detect_faces') as mock_detect:
                    mock_detect.return_value = []
                    state = state_machine.update_state(np.zeros((1080, 1920, 3)), frame_num)
            
            frame_states.append(state)
        
        # Verify state changes
        state_values = [state.value for state in frame_states]
        self.assertIn("vert_focus", state_values)
        self.assertIn("bg_blur_rect", state_values)
        
        # Verify timeline
        timeline = state_machine.get_state_timeline()
        self.assertGreater(len(timeline), 1)  # Should have multiple states
    
    def test_caption_style_integration(self):
        """Test caption style integration with translation"""
        # Generate captions
        captions = [
            {"start": 0.0, "end": 2.0, "text": "Hello world"},
            {"start": 3.0, "end": 5.0, "text": "This is a test"}
        ]
        
        # Apply styling
        style_config = generate_caption_styles(CaptionStyle.BOXED_HIGH_CONTRAST)
        emphasized_captions = []
        
        for caption in captions:
            emphasized_text = emphasize_keywords(
                caption["text"], 
                ["test", "world"], 
                "bold"
            )
            emphasized_captions.append({
                **caption,
                "text": emphasized_text
            })
        
        # Verify emphasis applied
        self.assertIn("\\b1test\\b0", emphasized_captions[1]["text"])
        self.assertIn("\\b1world\\b0", emphasized_captions[0]["text"])
        
        # Test text wrapping
        wrapped_captions = []
        for caption in emphasized_captions:
            wrapped_text = wrap_caption_text(
                caption["text"],
                max_width_chars=15,
                max_lines=2
            )
            wrapped_captions.append({
                **caption,
                "text": wrapped_text
            })
        
        # Verify wrapping
        for caption in wrapped_captions:
            lines = caption["text"].split("\\N")
            self.assertLessEqual(len(lines), 2)
            for line in lines:
                self.assertLessEqual(len(line), 15)


if __name__ == "__main__":
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_suite.addTest(unittest.makeSuite(TestLayoutStateMachine))
    test_suite.addTest(unittest.makeSuite(TestCaptionStyles))
    test_suite.addTest(unittest.makeSuite(TestCaptionTranslation))
    test_suite.addTest(unittest.makeSuite(TestManifestGeneration))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
