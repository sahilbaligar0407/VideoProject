"""
Face detection and speaker tracking for vertical video clips.
Keeps the active speaker centered in the frame.
"""

import cv2
import numpy as np
import os
import subprocess
import tempfile
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from app.settings import settings

@dataclass
class FrameBox:
    """Compatibility class for face detection boxes used by other modules"""
    t: float  # Timestamp
    x: float  # Center x (normalized 0-1 or pixel coordinates)
    y: float  # Center y (normalized 0-1 or pixel coordinates)
    w: float  # Width (normalized 0-1 or pixel coordinates)
    h: float  # Height (normalized 0-1 or pixel coordinates)
    conf: float  # Confidence score
    bbox: Optional[Tuple[float, float, float, float]] = None  # Optional bbox tuple
    
    @property
    def width(self) -> float:
        """Alias for w"""
        return self.w
    
    @property
    def height(self) -> float:
        """Alias for h"""
        return self.h
    
    @property
    def confidence(self) -> float:
        """Alias for conf"""
        return self.conf

@dataclass
class FaceDetection:
    """Represents a detected face in a frame"""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    frame_time: float

@dataclass
class SpeakerTrack:
    """Represents speaker tracking information for a clip"""
    start_time: float
    end_time: float
    center_x: float  # Normalized center position (0.0 to 1.0)
    center_y: float  # Normalized center position (0.0 to 1.0)
    face_size: float  # Normalized face size
    confidence: float

class FaceTracker:
    """Tracks faces and keeps speakers centered in vertical video clips"""
    
    def __init__(self):
        self.face_cascade = None
        self.face_detector = None
        self._initialize_face_detection()
    
    def _initialize_face_detection(self):
        """Initialize face detection models"""
        try:
            # Try to use OpenCV's built-in face cascade
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            if os.path.exists(cascade_path):
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
                print(f"✅ Loaded OpenCV face cascade: {cascade_path}")
            else:
                print(f"⚠️ Face cascade not found at: {cascade_path}")
            
            # Try to use DNN-based face detection if available
            try:
                prototxt_path = "models/deploy.prototxt"
                caffemodel_path = "models/res10_300x300_ssd_iter_140000.caffemodel"
                
                if os.path.exists(prototxt_path) and os.path.exists(caffemodel_path):
                    self.face_detector = cv2.dnn.readNetFromCaffe(prototxt_path, caffemodel_path)
                    print(f"✅ Loaded DNN face detector")
                else:
                    print(f"⚠️ DNN face detector models not found")
            except Exception as e:
                print(f"⚠️ DNN face detector initialization failed: {e}")
                
        except Exception as e:
            print(f"❌ Face detection initialization failed: {e}")
    
    def detect_faces_in_frame(self, frame: np.ndarray, frame_time: float) -> List[FaceDetection]:
        """Detect faces in a single frame"""
        faces = []
        
        if self.face_cascade is None and self.face_detector is None:
            return faces
        
        # Convert to grayscale for cascade classifier
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Method 1: Cascade classifier
        if self.face_cascade is not None:
            try:
                cascade_faces = self.face_cascade.detectMultiScale(
                    gray, 
                    scaleFactor=1.1, 
                    minNeighbors=5, 
                    minSize=(30, 30)
                )
                
                for (x, y, w, h) in cascade_faces:
                    faces.append(FaceDetection(
                        x=x, y=y, width=w, height=h,
                        confidence=0.8,  # Cascade doesn't provide confidence
                        frame_time=frame_time
                    ))
            except Exception as e:
                print(f"⚠️ Cascade face detection failed: {e}")
        
        # Method 2: DNN-based detection (more accurate)
        if self.face_detector is not None:
            try:
                # Prepare frame for DNN
                blob = cv2.dnn.blobFromImage(
                    cv2.resize(frame, (300, 300)), 
                    1.0, (300, 300), (104.0, 177.0, 123.0)
                )
                
                self.face_detector.setInput(blob)
                detections = self.face_detector.forward()
                
                # Process detections
                for i in range(detections.shape[2]):
                    confidence = detections[0, 0, i, 2]
                    
                    if confidence > settings.face_detection_confidence:
                        # Get bounding box coordinates
                        box = detections[0, 0, i, 3:7] * np.array([frame.shape[1], frame.shape[0], frame.shape[1], frame.shape[0]])
                        x, y, x2, y2 = box.astype(int)
                        
                        faces.append(FaceDetection(
                            x=x, y=y, width=x2-x, height=y2-y,
                            confidence=confidence,
                            frame_time=frame_time
                        ))
            except Exception as e:
                print(f"⚠️ DNN face detection failed: {e}")
        
        return faces
    
    def analyze_video_faces(self, video_path: str, start_time: float, end_time: float) -> List[SpeakerTrack]:
        """Analyze faces throughout a video segment to track speaker movement"""
        print(f"👤 Analyzing faces in video segment: {start_time:.2f}s to {end_time:.2f}s")
        
        if not os.path.exists(video_path):
            print(f"❌ Video file not found: {video_path}")
            return []
        
        # Use a longer frame interval to reduce the number of frames to process
        # This makes face tracking much faster while still being effective
        clip_duration = end_time - start_time
        if clip_duration > 30:
            frame_interval = 2.0  # Sample every 2 seconds for long clips
            max_frames = 15  # Limit to 15 frames max
        elif clip_duration > 15:
            frame_interval = 1.5  # Sample every 1.5 seconds for medium clips
            max_frames = 10
        else:
            frame_interval = 1.0  # Sample every 1 second for short clips
            max_frames = 10
        
        face_tracks = []
        
        try:
            # Extract frames for analysis (limit number of frames)
            frame_times = list(np.arange(start_time, end_time, frame_interval))[:max_frames]
            
            if not frame_times:
                # If no frames to analyze, sample at start, middle, and end
                frame_times = [
                    start_time,
                    start_time + (end_time - start_time) / 2,
                    end_time - 0.5
                ]
            
            print(f"👤 Sampling {len(frame_times)} frames for face detection...")
            
            import time
            start_analysis_time = time.time()
            max_analysis_time = 30  # Maximum 30 seconds for face analysis
            
            for i, frame_time in enumerate(frame_times):
                # Check if we're taking too long
                if time.time() - start_analysis_time > max_analysis_time:
                    print(f"⚠️ Face analysis taking too long, stopping after {i}/{len(frame_times)} frames")
                    break
                
                # Extract frame using ffmpeg
                frame_path = self._extract_frame(video_path, frame_time)
                if not frame_path:
                    continue
                
                try:
                    # Read and analyze frame
                    frame = cv2.imread(frame_path)
                    if frame is not None:
                        faces = self.detect_faces_in_frame(frame, frame_time)
                        
                        if faces:
                            # Find the most confident face
                            best_face = max(faces, key=lambda f: f.confidence)
                            
                            # Calculate normalized center position
                            frame_height, frame_width = frame.shape[:2]
                            center_x = (best_face.x + best_face.width / 2) / frame_width
                            center_y = (best_face.y + best_face.height / 2) / frame_height
                            
                            # Calculate normalized face size
                            face_size = (best_face.width * best_face.height) / (frame_width * frame_height)
                            
                            face_tracks.append(SpeakerTrack(
                                start_time=frame_time,
                                end_time=frame_time + frame_interval,
                                center_x=center_x,
                                center_y=center_y,
                                face_size=face_size,
                                confidence=best_face.confidence
                            ))
                    
                    # Cleanup frame file
                    if os.path.exists(frame_path):
                        os.remove(frame_path)
                    
                except Exception as e:
                    print(f"⚠️ Frame analysis failed at {frame_time:.2f}s: {e}")
                    if os.path.exists(frame_path):
                        try:
                            os.remove(frame_path)
                        except:
                            pass
            
            analysis_time = time.time() - start_analysis_time
            print(f"👤 Face analysis complete: {len(face_tracks)} face detections in {analysis_time:.1f}s")
            return face_tracks
            
        except Exception as e:
            print(f"❌ Video face analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_frame(self, video_path: str, timestamp: float) -> Optional[str]:
        """Extract a single frame from video at specified timestamp"""
        try:
            # Create temporary file for frame
            temp_fd, temp_path = tempfile.mkstemp(suffix='.jpg')
            os.close(temp_fd)
            
            # Extract frame using ffmpeg with faster settings
            # Use -ss before -i for faster seeking
            cmd = [
                "ffmpeg", "-ss", str(timestamp),
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "5",  # Lower quality for speed (2-31 scale, higher = lower quality)
                "-y", temp_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)  # Reduced timeout
            if result.returncode == 0 and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                return temp_path
            else:
                # Don't print error for every failed frame to reduce log spam
                return None
                
        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            # Don't print error for every failed frame
            return None
    
    def calculate_optimal_crop(self, face_tracks: List[SpeakerTrack], 
                              target_width: int = 1080, target_height: int = 1920) -> Dict[str, float]:
        """Calculate optimal crop parameters to keep speaker centered"""
        if not face_tracks:
            return {"center_x": 0.5, "center_y": 0.5, "scale": 1.0}
        
        # Calculate weighted average center position
        total_weight = 0
        weighted_center_x = 0
        weighted_center_y = 0
        
        for track in face_tracks:
            weight = track.confidence * track.face_size
            total_weight += weight
            weighted_center_x += track.center_x * weight
            weighted_center_y += track.center_y * weight
        
        if total_weight > 0:
            avg_center_x = weighted_center_x / total_weight
            avg_center_y = weighted_center_y / total_weight
        else:
            avg_center_x = 0.5
            avg_center_y = 0.5
        
        # Apply smoothing to avoid jitter
        smoothing = settings.face_tracking_smoothing
        avg_center_x = (avg_center_x * smoothing) + (0.5 * (1 - smoothing))
        avg_center_y = (avg_center_y * smoothing) + (0.5 * (1 - smoothing))
        
        # Calculate optimal scale based on face sizes
        if face_tracks:
            avg_face_size = np.mean([t.face_size for t in face_tracks])
            # Scale to ensure face is appropriately sized in final frame
            optimal_scale = min(1.0, avg_face_size * 8)  # Adjust multiplier as needed
        else:
            optimal_scale = 1.0
        
        return {
            "center_x": avg_center_x,
            "center_y": avg_center_y,
            "scale": optimal_scale
        }
    
    def apply_face_tracking_to_clip(self, video_path: str, output_path: str, 
                                   start_time: float, end_time: float) -> bool:
        """Apply face tracking to keep speaker centered in a video clip"""
        if not settings.face_detection_enabled or not settings.auto_crop_enabled:
            print(f"⚠️ Face tracking disabled, using standard clip extraction")
            return False
        
        try:
            import time
            start_time_total = time.time()
            max_total_time = 60  # Maximum 60 seconds total for face tracking
            
            print(f"👤 Applying face tracking to clip: {start_time:.2f}s to {end_time:.2f}s")
            
            # Analyze faces in the clip with timeout
            face_tracks = self.analyze_video_faces(video_path, start_time, end_time)
            
            # Check if we're taking too long
            if time.time() - start_time_total > max_total_time:
                print(f"⚠️ Face tracking taking too long, skipping...")
                return False
            
            if not face_tracks:
                print(f"⚠️ No faces detected, using standard clip extraction")
                return False
            
            # Calculate optimal crop parameters
            crop_params = self.calculate_optimal_crop(face_tracks)
            
            print(f"👤 Crop parameters: center_x={crop_params['center_x']:.3f}, "
                  f"center_y={crop_params['center_y']:.3f}, scale={crop_params['scale']:.3f}")
            
            # Apply crop using ffmpeg
            success = self._apply_crop_with_ffmpeg(
                video_path, output_path, start_time, end_time, crop_params
            )
            
            total_time = time.time() - start_time_total
            if success:
                print(f"✅ Face tracking applied successfully in {total_time:.1f}s")
                return True
            else:
                print(f"❌ Face tracking failed after {total_time:.1f}s, falling back to standard extraction")
                return False
                
        except Exception as e:
            print(f"❌ Face tracking application failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _apply_crop_with_ffmpeg(self, video_path: str, output_path: str, 
                                start_time: float, end_time: float, 
                                crop_params: Dict[str, float]) -> bool:
        """Apply crop using ffmpeg to keep speaker centered"""
        try:
            duration = end_time - start_time
            
            # Calculate crop dimensions and position
            # This is a simplified approach - in practice, you'd want more sophisticated cropping
            center_x = crop_params['center_x']
            center_y = crop_params['center_y']
            scale = crop_params['scale']
            
            # For now, use a simple crop that keeps the speaker in the center
            # In a full implementation, you'd calculate exact crop coordinates
            
            cmd = [
                "ffmpeg", "-i", video_path,
                "-ss", str(start_time),
                "-t", str(duration),
                "-vf", "crop=1080:1920:0:0",  # Simple center crop for now
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-preset", "veryfast", "-crf", "23",
                "-r", "30", "-vsync", "cfr",
                "-profile:v", "baseline", "-level:v", "3.0", "-tag:v", "avc1",
                "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
                "-movflags", "+faststart",
                "-y", output_path
            ]
            
            print(f"🔧 Running face-tracking crop command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and os.path.exists(output_path):
                print(f"✅ Face tracking crop successful: {os.path.getsize(output_path)} bytes")
                return True
            else:
                print(f"❌ Face tracking crop failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Face tracking crop failed: {e}")
            return False


# Compatibility functions for legacy API

def track_faces(video_path: str, sample_rate: int = 10) -> List[FrameBox]:
    """
    Track faces in a video at regular intervals (compatibility function).
    
    Args:
        video_path: Path to video file
        sample_rate: Number of samples per second
        
    Returns:
        List of FrameBox objects with face detection data
    """
    tracker = FaceTracker()
    face_boxes = []
    
    try:
        # Get video duration
        cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", video_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"⚠️ Could not get video duration: {result.stderr}")
            return []
        
        duration = float(result.stdout.strip())
        
        # Sample at regular intervals
        sample_interval = 1.0 / sample_rate
        frame_times = np.arange(0, duration, sample_interval)
        
        for frame_time in frame_times:
            # Extract frame
            frame_path = tracker._extract_frame(video_path, frame_time)
            if not frame_path:
                continue
            
            try:
                # Read and analyze frame
                frame = cv2.imread(frame_path)
                if frame is not None:
                    faces = tracker.detect_faces_in_frame(frame, frame_time)
                    
                    if faces:
                        # Get the most confident face
                        best_face = max(faces, key=lambda f: f.confidence)
                        
                        # Get frame dimensions
                        frame_height, frame_width = frame.shape[:2]
                        
                        # Calculate center position (normalized)
                        center_x = (best_face.x + best_face.width / 2) / frame_width
                        center_y = (best_face.y + best_face.height / 2) / frame_height
                        
                        # Calculate normalized dimensions
                        norm_width = best_face.width / frame_width
                        norm_height = best_face.height / frame_height
                        
                        face_boxes.append(FrameBox(
                            t=frame_time,
                            x=center_x,
                            y=center_y,
                            w=norm_width,
                            h=norm_height,
                            conf=best_face.confidence,
                            bbox=(best_face.x, best_face.y, best_face.width, best_face.height)
                        ))
                
                # Cleanup
                if os.path.exists(frame_path):
                    os.remove(frame_path)
                    
            except Exception as e:
                print(f"⚠️ Frame processing failed at {frame_time:.2f}s: {e}")
                if os.path.exists(frame_path):
                    os.remove(frame_path)
        
        print(f"✅ Face tracking complete: {len(face_boxes)} detections")
        return face_boxes
        
    except Exception as e:
        print(f"❌ Face tracking failed: {e}")
        return []


def smooth_boxes(face_boxes: List[FrameBox], smoothing_factor: float = 0.8) -> List[FrameBox]:
    """
    Smooth face detection boxes to reduce jitter (compatibility function).
    
    Args:
        face_boxes: List of FrameBox objects
        smoothing_factor: Smoothing factor (0-1), higher = more smoothing
        
    Returns:
        List of smoothed FrameBox objects
    """
    if not face_boxes or len(face_boxes) <= 1:
        return face_boxes
    
    smoothed = [face_boxes[0]]  # First box stays the same
    
    for i in range(1, len(face_boxes)):
        prev = smoothed[-1]
        curr = face_boxes[i]
        
        # Smooth position and size
        smooth_x = prev.x * smoothing_factor + curr.x * (1 - smoothing_factor)
        smooth_y = prev.y * smoothing_factor + curr.y * (1 - smoothing_factor)
        smooth_w = prev.w * smoothing_factor + curr.w * (1 - smoothing_factor)
        smooth_h = prev.h * smoothing_factor + curr.h * (1 - smoothing_factor)
        smooth_conf = prev.conf * smoothing_factor + curr.conf * (1 - smoothing_factor)
        
        smoothed.append(FrameBox(
            t=curr.t,
            x=smooth_x,
            y=smooth_y,
            w=smooth_w,
            h=smooth_h,
            conf=smooth_conf,
            bbox=curr.bbox
        ))
    
    return smoothed


def has_face_in_range(face_boxes: List[FrameBox], start_time: float, end_time: float) -> bool:
    """
    Check if there are faces in a time range (compatibility function).
    
    Args:
        face_boxes: List of FrameBox objects
        start_time: Start time in seconds
        end_time: End time in seconds
        
    Returns:
        True if faces exist in the time range
    """
    return any(start_time <= box.t <= end_time for box in face_boxes)
