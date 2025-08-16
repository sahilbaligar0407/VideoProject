"""
Face detection and tracking for ClipGenius Pipeline v2.
Uses MediaPipe for fast, CPU-friendly face detection with BYTE tracking.
"""

import cv2
import numpy as np
import mediapipe as mp
from dataclasses import dataclass
from typing import List, Tuple, Optional
import subprocess
import json
import os
from app.settings import settings

@dataclass
class FrameBox:
    """Face detection result for a single frame"""
    t: float          # timestamp in seconds
    x: int            # center x coordinate
    y: int            # center y coordinate  
    w: int            # width
    h: int            # height
    conf: float       # confidence score

class FaceTracker:
    """Face detection and tracking using MediaPipe + BYTE tracking"""
    
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_detection = None
        self.tracks = {}  # track_id -> [FrameBox]
        self.next_track_id = 0
        
    def _init_mediapipe(self):
        """Initialize MediaPipe face detection"""
        if self.face_detection is None:
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=1,  # 0=short-range, 1=full-range
                min_detection_confidence=0.5
            )
    
    def _detect_faces_in_frame(self, frame: np.ndarray, timestamp: float) -> List[FrameBox]:
        """Detect faces in a single frame"""
        self._init_mediapipe()
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb_frame)
        
        faces = []
        if results.detections:
            h, w = frame.shape[:2]
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                
                # Convert relative coordinates to absolute
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                
                # Get confidence
                confidence = detection.score[0]
                
                # Create FrameBox with center coordinates
                face = FrameBox(
                    t=timestamp,
                    x=x + width // 2,  # center x
                    y=y + height // 2,  # center y
                    w=width,
                    h=height,
                    conf=confidence
                )
                faces.append(face)
        
        return faces
    
    def _iou(self, box1: FrameBox, box2: FrameBox) -> float:
        """Calculate Intersection over Union between two boxes"""
        # Convert to x1,y1,x2,y2 format
        x1_1, y1_1 = box1.x - box1.w//2, box1.y - box1.h//2
        x2_1, y2_1 = box1.x + box1.w//2, box1.y + box1.h//2
        
        x1_2, y1_2 = box2.x - box2.w//2, box2.y - box2.h//2
        x2_2, y2_2 = box2.x + box2.w//2, box2.y + box2.h//2
        
        # Calculate intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        union = box1.w * box1.h + box2.w * box2.h - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _update_tracks(self, faces: List[FrameBox], timestamp: float):
        """Update existing tracks with new detections using simple IOU tracking"""
        if not faces:
            # No faces detected, mark all tracks as inactive
            for track_id in list(self.tracks.keys()):
                if timestamp - self.tracks[track_id][-1].t > 0.5:  # 500ms timeout
                    del self.tracks[track_id]
            return
        
        # Match detections to existing tracks
        matched_tracks = set()
        matched_faces = set()
        
        for track_id, track_boxes in self.tracks.items():
            if not track_boxes:
                continue
                
            last_box = track_boxes[-1]
            best_iou = 0
            best_face_idx = -1
            
            for i, face in enumerate(faces):
                if i in matched_faces:
                    continue
                    
                iou = self._iou(last_box, face)
                if iou > best_iou and iou > 0.3:  # IOU threshold
                    best_iou = iou
                    best_face_idx = i
            
            if best_face_idx >= 0:
                # Update existing track
                self.tracks[track_id].append(faces[best_face_idx])
                matched_tracks.add(track_id)
                matched_faces.add(best_face_idx)
        
        # Create new tracks for unmatched detections
        for i, face in enumerate(faces):
            if i not in matched_faces:
                track_id = self.next_track_id
                self.next_track_id += 1
                self.tracks[track_id] = [face]
    
    def track_faces_video(self, video_path: str, sample_rate: int = 10) -> List[FrameBox]:
        """
        Track faces throughout a video file
        
        Args:
            video_path: Path to video file
            sample_rate: Sample every Nth frame (default: 10 = 3fps for 30fps video)
            
        Returns:
            List of FrameBox objects with timestamps
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Could not open video: {video_path}")
            return []
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        print(f"🎬 Tracking faces in {video_path}")
        print(f"   FPS: {fps:.1f}, Duration: {duration:.1f}s, Total frames: {total_frames}")
        
        frame_count = 0
        all_faces = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Sample every Nth frame
            if frame_count % sample_rate == 0:
                timestamp = frame_count / fps
                
                # Detect faces in this frame
                faces = self._detect_faces_in_frame(frame, timestamp)
                
                # Update tracking
                self._update_tracks(faces, timestamp)
                
                # Add all current detections to output
                for track_boxes in self.tracks.values():
                    if track_boxes:
                        all_faces.append(track_boxes[-1])
                
                if frame_count % (sample_rate * 10) == 0:
                    print(f"   Frame {frame_count}/{total_frames} ({timestamp:.1f}s): {len(faces)} faces")
            
            frame_count += 1
        
        cap.release()
        
        # Sort by timestamp
        all_faces.sort(key=lambda x: x.t)
        
        print(f"✅ Face tracking complete: {len(all_faces)} detections")
        return all_faces

def track_faces(video_path: str, sample_rate: int = 10) -> List[FrameBox]:
    """Main function to track faces in a video"""
    tracker = FaceTracker()
    return tracker.track_faces_video(video_path, sample_rate)

def smooth_boxes(boxes: List[FrameBox], window_size: int = 5) -> List[FrameBox]:
    """
    Smooth face tracking boxes using exponential moving average
    
    Args:
        boxes: List of FrameBox objects
        window_size: Smoothing window size
        
    Returns:
        Smoothed list of FrameBox objects
    """
    if not boxes or len(boxes) < 2:
        return boxes
    
    smoothed = []
    alpha = 2.0 / (window_size + 1)  # EMA smoothing factor
    
    # Initialize with first box
    smoothed.append(boxes[0])
    
    for i in range(1, len(boxes)):
        prev = smoothed[-1]
        curr = boxes[i]
        
        # Smooth coordinates and dimensions
        smooth_x = int(alpha * curr.x + (1 - alpha) * prev.x)
        smooth_y = int(alpha * curr.y + (1 - alpha) * prev.y)
        smooth_w = int(alpha * curr.w + (1 - alpha) * prev.w)
        smooth_h = int(alpha * curr.h + (1 - alpha) * prev.h)
        
        # Keep original timestamp and confidence
        smooth_box = FrameBox(
            t=curr.t,
            x=smooth_x,
            y=smooth_y,
            w=smooth_w,
            h=smooth_h,
            conf=curr.conf
        )
        smoothed.append(smooth_box)
    
    return smoothed

def slice_boxes(boxes: List[FrameBox], start_time: float, end_time: float) -> List[FrameBox]:
    """Get face boxes within a time range"""
    return [box for box in boxes if start_time <= box.t <= end_time]

def has_face_in_range(boxes: List[FrameBox], start_time: float, end_time: float, min_confidence: float = 0.5) -> bool:
    """Check if there are confident face detections in a time range"""
    range_boxes = slice_boxes(boxes, start_time, end_time)
    return any(box.conf >= min_confidence for box in range_boxes)
