"""
Dynamic layout state machine for ClipGenius Pipeline v2.
Handles automatic switching between VERT_FOCUS (face tracking) and BG_BLUR_RECT (background blur)
with smooth transitions and scene-cut safety.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import cv2
import mediapipe as mp

class LayoutState(Enum):
    """Layout states for dynamic video rendering"""
    VERT_FOCUS = "vert_focus"      # Face tracking with auto-reframe
    BG_BLUR_RECT = "bg_blur_rect"  # Blurred background with foreground rectangle
    GAMEPLAY = "gameplay"          # Gameplay background with foreground overlay

@dataclass
class FaceTrack:
    """Represents a tracked face with speaking score and metadata"""
    track_id: int
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    confidence: float
    speaking_score: float = 0.0
    frame_count: int = 0
    first_seen: int = 0
    last_seen: int = 0
    
    @property
    def area(self) -> int:
        return self.bbox[2] * self.bbox[3]
    
    @property
    def center(self) -> Tuple[int, int]:
        x, y, w, h = self.bbox
        return (x + w // 2, y + h // 2)

@dataclass
class StateTransition:
    """Represents a state transition with timing and parameters"""
    from_state: LayoutState
    to_state: LayoutState
    start_frame: int
    end_frame: int
    transition_duration: float = 0.4  # seconds
    transition_type: str = "zoom"     # zoom, crossfade, slide

class LayoutStateMachine:
    """State machine for dynamic layout switching"""
    
    def __init__(self, 
                 face_confidence_threshold: float = 0.7,
                 state_debounce_frames: int = 12,
                 min_face_size: int = 100,
                 scene_cut_threshold: float = 0.3):
        
        self.face_confidence_threshold = face_confidence_threshold
        self.state_debounce_frames = state_debounce_frames
        self.min_face_size = min_face_size
        self.scene_cut_threshold = scene_cut_threshold
        
        # State tracking
        self.current_state = LayoutState.BG_BLUR_RECT
        self.state_start_frame = 0
        self.face_detection_count = 0
        self.no_face_count = 0
        
        # Face tracking
        self.face_tracks: Dict[int, FaceTrack] = {}
        self.next_track_id = 0
        
        # Speech segments for speaking score computation
        self.speech_segments: List[Dict[str, Any]] = []
        
        # State history
        self.state_history: List[StateTransition] = []
        
        # Scene cut detection
        self.last_frame_features = None
        self.scene_cut_detected = False
        
        # MediaPipe face detection
        self.mp_face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=1,  # 0=short-range, 1=full-range
            min_detection_confidence=0.5
        )
    
    def update_speech_segments(self, speech_segments: List[Dict[str, Any]]):
        """Update speech segments for speaking score computation"""
        self.speech_segments = speech_segments
    
    def compute_speaking_score(self, face_bbox: Tuple[int, int, int, int], 
                             frame_time: float) -> float:
        """Compute speaking score based on face overlap with speech segments"""
        if not self.speech_segments:
            return 0.0
        
        face_center_x = face_bbox[0] + face_bbox[2] // 2
        face_center_y = face_bbox[1] + face_bbox[3] // 2
        
        # Find speech segments that overlap with this frame
        overlapping_speech = 0.0
        total_speech = 0.0
        
        for segment in self.speech_segments:
            start_time = segment.get('start', 0)
            end_time = segment.get('end', 0)
            
            if start_time <= frame_time <= end_time:
                total_speech += 1.0
                # Check if face is in speech region (simplified: assume center of frame)
                # In a real implementation, you'd map speech to screen coordinates
                overlapping_speech += 1.0
        
        if total_speech == 0:
            return 0.0
        
        return overlapping_speech / total_speech
    
    def detect_faces(self, frame: np.ndarray, frame_number: int) -> List[FaceTrack]:
        """Detect faces in the current frame using MediaPipe"""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        results = self.mp_face_detection.process(rgb_frame)
        
        detected_faces = []
        
        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                confidence = detection.score[0]
                
                if confidence < self.face_confidence_threshold:
                    continue
                
                # Convert relative coordinates to absolute
                h, w = frame.shape[:2]
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                
                # Ensure bbox is within frame bounds
                x = max(0, x)
                y = max(0, y)
                width = min(width, w - x)
                height = min(height, h - y)
                
                if width < self.min_face_size or height < self.min_face_size:
                    continue
                
                # Check if this face matches an existing track
                matched_track = self._match_face_to_track((x, y, width, height))
                
                if matched_track:
                    # Update existing track
                    matched_track.bbox = (x, y, width, height)
                    matched_track.confidence = confidence
                    matched_track.frame_count += 1
                    matched_track.last_seen = frame_number
                    matched_track.speaking_score = self.compute_speaking_score(
                        (x, y, width, height), frame_number / 30.0  # Assume 30fps
                    )
                    detected_faces.append(matched_track)
                else:
                    # Create new track
                    new_track = FaceTrack(
                        track_id=self.next_track_id,
                        bbox=(x, y, width, height),
                        confidence=confidence,
                        frame_count=1,
                        first_seen=frame_number,
                        last_seen=frame_number
                    )
                    new_track.speaking_score = self.compute_speaking_score(
                        (x, y, width, height), frame_number / 30.0
                    )
                    
                    self.face_tracks[self.next_track_id] = new_track
                    self.next_track_id += 1
                    detected_faces.append(new_track)
        
        return detected_faces
    
    def _match_face_to_track(self, bbox: Tuple[int, int, int, int]) -> Optional[FaceTrack]:
        """Match a detected face to an existing track using IoU"""
        best_match = None
        best_iou = 0.0
        
        for track in self.face_tracks.values():
            iou = self._compute_iou(bbox, track.bbox)
            if iou > 0.5 and iou > best_iou:  # IoU threshold
                best_match = track
                best_iou = iou
        
        return best_match
    
    def _compute_iou(self, bbox1: Tuple[int, int, int, int], 
                     bbox2: Tuple[int, int, int, int]) -> float:
        """Compute Intersection over Union between two bounding boxes"""
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        # Calculate intersection
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        intersection = (x_right - x_left) * (y_bottom - y_top)
        
        # Calculate union
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def select_primary_face(self, detected_faces: List[FaceTrack]) -> Optional[FaceTrack]:
        """Select the primary face based on speaking score, longevity, and size"""
        if not detected_faces:
            return None
        
        # Sort by speaking score (descending), then longevity, then size
        sorted_faces = sorted(
            detected_faces,
            key=lambda f: (
                f.speaking_score,
                f.frame_count,
                f.area
            ),
            reverse=True
        )
        
        return sorted_faces[0]
    
    def detect_scene_cut(self, frame: np.ndarray, frame_number: int) -> bool:
        """Detect hard scene cuts using feature matching"""
        if self.last_frame_features is None:
            self.last_frame_features = self._extract_frame_features(frame)
            return False
        
        current_features = self._extract_frame_features(frame)
        
        # Compute feature similarity
        similarity = self._compute_feature_similarity(
            self.last_frame_features, current_features
        )
        
        # Update last frame features
        self.last_frame_features = current_features
        
        # Detect scene cut if similarity is below threshold
        scene_cut = similarity < self.scene_cut_threshold
        
        if scene_cut:
            self.scene_cut_detected = True
            print(f"🎬 Scene cut detected at frame {frame_number}")
        
        return scene_cut
    
    def _extract_frame_features(self, frame: np.ndarray) -> np.ndarray:
        """Extract frame features for scene cut detection"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Resize for faster processing
        small = cv2.resize(gray, (64, 64))
        
        # Compute histogram
        hist = cv2.calcHist([small], [0], None, [64], [0, 256])
        
        # Normalize
        hist = cv2.normalize(hist, hist).flatten()
        
        return hist
    
    def _compute_feature_similarity(self, features1: np.ndarray, 
                                  features2: np.ndarray) -> float:
        """Compute similarity between two feature vectors"""
        # Use correlation coefficient
        correlation = np.corrcoef(features1, features2)[0, 1]
        return correlation if not np.isnan(correlation) else 0.0
    
    def update_state(self, frame: np.ndarray, frame_number: int, 
                    background_mode: str = "blur") -> LayoutState:
        """Update the current layout state based on face detection"""
        # Detect faces in current frame
        detected_faces = self.detect_faces(frame, frame_number)
        
        # Detect scene cuts
        scene_cut = self.detect_scene_cut(frame, frame_number)
        
        # Select primary face
        primary_face = self.select_primary_face(detected_faces)
        
        # Update face detection counters
        if primary_face and primary_face.confidence >= self.face_confidence_threshold:
            self.face_detection_count += 1
            self.no_face_count = 0
        else:
            self.no_face_count += 1
            self.face_detection_count = 0
        
        # Determine target state
        target_state = self._determine_target_state(primary_face, background_mode)
        
        # Handle state transitions
        if target_state != self.current_state:
            self._transition_state(target_state, frame_number, scene_cut)
        
        return self.current_state
    
    def _determine_target_state(self, primary_face: Optional[FaceTrack], 
                              background_mode: str) -> LayoutState:
        """Determine the target state based on face detection and background mode"""
        if primary_face and self.face_detection_count >= self.state_debounce_frames:
            return LayoutState.VERT_FOCUS
        elif self.no_face_count >= self.state_debounce_frames:
            if background_mode == "gameplay":
                return LayoutState.GAMEPLAY
            else:
                return LayoutState.BG_BLUR_RECT
        else:
            # Keep current state during debounce period
            return self.current_state
    
    def _transition_state(self, new_state: LayoutState, frame_number: int, 
                         scene_cut: bool):
        """Handle state transition with logging and history"""
        old_state = self.current_state
        
        # Record transition
        transition = StateTransition(
            from_state=old_state,
            to_state=new_state,
            start_frame=frame_number,
            end_frame=frame_number + int(0.4 * 30),  # 0.4s transition at 30fps
            transition_duration=0.4,
            transition_type="zoom"
        )
        
        self.state_history.append(transition)
        
        # Update current state
        self.current_state = new_state
        self.state_start_frame = frame_number
        
        # Reset scene cut flag
        if scene_cut:
            self.scene_cut_detected = False
        
        print(f"🔄 State transition: {old_state.value} → {new_state.value} at frame {frame_number}")
    
    def get_current_layout_config(self) -> Dict[str, Any]:
        """Get current layout configuration for rendering"""
        primary_face = None
        if self.current_state == LayoutState.VERT_FOCUS:
            # Find the most recent primary face
            detected_faces = [f for f in self.face_tracks.values() 
                            if f.frame_count > 0]
            if detected_faces:
                primary_face = self.select_primary_face(detected_faces)
        
        return {
            "state": self.current_state.value,
            "primary_face": {
                "bbox": primary_face.bbox if primary_face else None,
                "track_id": primary_face.track_id if primary_face else None,
                "speaking_score": primary_face.speaking_score if primary_face else 0.0
            } if primary_face else None,
            "scene_cut_detected": self.scene_cut_detected,
            "state_duration_frames": self.state_start_frame,
            "face_tracks_count": len(self.face_tracks)
        }
    
    def get_state_timeline(self) -> List[Dict[str, Any]]:
        """Get timeline of state changes for manifest generation"""
        timeline = []
        
        for i, transition in enumerate(self.state_history):
            timeline.append({
                "frame_start": transition.start_frame,
                "frame_end": transition.end_frame if i < len(self.state_history) - 1 else None,
                "state": transition.from_state.value,
                "transition_type": transition.transition_type,
                "transition_duration": transition.transition_duration
            })
        
        # Add current state
        timeline.append({
            "frame_start": self.state_start_frame,
            "frame_end": None,
            "state": self.current_state.value,
            "transition_type": None,
            "transition_duration": None
        })
        
        return timeline
    
    def cleanup(self):
        """Clean up resources"""
        self.mp_face_detection.close()
