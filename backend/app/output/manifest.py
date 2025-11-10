"""
Output manifest generation for ClipGenius Pipeline v2.
Creates detailed metadata files alongside generated clips.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.layout.state_machine import LayoutStateMachine, LayoutState

def generate_clip_manifest(
    clip_id: str,
    source_video: str,
    start_time: float,
    end_time: float,
    duration: float,
    output_path: str,
    layout_states: List[Dict[str, Any]],
    transcript_info: Dict[str, Any],
    processing_metadata: Dict[str, Any],
    output_dir: str = "outputs"
) -> str:
    """
    Generate a comprehensive manifest file for a clip.
    
    Args:
        clip_id: Unique identifier for the clip
        source_video: Path to source video file
        start_time: Start time in source video (seconds)
        end_time: End time in source video (seconds)
        duration: Clip duration (seconds)
        output_path: Path to generated clip file
        layout_states: List of layout state changes during clip
        transcript_info: Transcript file information
        processing_metadata: Additional processing metadata
        output_dir: Output directory for manifest
        
    Returns:
        Path to generated manifest file
    """
    
    # Create manifest data structure
    manifest = {
        "clip_id": clip_id,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "version": "2.0.0",
        
        # Source video information
        "source": {
            "video_path": source_video,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "extraction_method": "smart_clipping"
        },
        
        # Output information
        "output": {
            "video_path": output_path,
            "format": "mp4",
            "codec": "h264",
            "resolution": "1080x1920",
            "aspect_ratio": "9:16",
            "frame_rate": 30,
            "bitrate": "variable"
        },
        
        # Layout and rendering information
        "layout": {
            "mode": "dynamic",
            "states": layout_states,
            "state_timeline": _extract_state_timeline(layout_states),
            "transitions": _extract_transitions(layout_states),
            "face_tracking": _extract_face_tracking_info(layout_states)
        },
        
        # Transcript file information
        "transcripts": {
            "enabled": transcript_info.get("enabled", True),
            "files": _generate_transcript_file_list(transcript_info, clip_id, output_dir)
        },
        
        # Processing metadata
        "processing": {
            "engine": "ClipGenius Pipeline v2",
            "ai_models": {
                "transcription": "whisper-1",
                "embeddings": "text-embedding-3-small",
                "translation": "gpt-4o-mini"
            },
            "highlight_detection": processing_metadata.get("highlight_detection", {}),
            "viral_scoring": processing_metadata.get("viral_scoring", {}),
            "processing_time": processing_metadata.get("processing_time", 0),
            "ffmpeg_commands": processing_metadata.get("ffmpeg_commands", [])
        },
        
        # Quality metrics
        "quality": {
            "vertical_rendering": _assess_vertical_quality(layout_states),
            "overall_score": _assess_vertical_quality(layout_states).get("score", 0)
        },
        
        # File integrity
        "integrity": {
            "video_file_size": _get_file_size(output_path),
            "video_file_hash": _calculate_file_hash(output_path),
            "transcript_files": _verify_transcript_files(transcript_info, clip_id, output_dir)
        }
    }
    
    # Generate manifest file path
    manifest_filename = f"{clip_id}_manifest.json"
    manifest_path = os.path.join(output_dir, manifest_filename)
    
    # Write manifest file
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Generated manifest: {manifest_path}")
        return manifest_path
        
    except Exception as e:
        print(f"❌ Failed to generate manifest: {e}")
        return ""

def _extract_state_timeline(layout_states: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract timeline of state changes from layout states"""
    timeline = []
    
    for state in layout_states:
        timeline.append({
            "frame": state.get("frame", 0),
            "state": state.get("state", "unknown"),
            "timestamp": state.get("frame", 0) / 30.0,  # Assume 30fps
            "primary_face": state.get("config", {}).get("primary_face"),
            "scene_cut": state.get("config", {}).get("scene_cut_detected", False)
        })
    
    return timeline

def _extract_transitions(layout_states: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract state transitions from layout states"""
    transitions = []
    
    for i in range(1, len(layout_states)):
        prev_state = layout_states[i-1]
        curr_state = layout_states[i]
        
        if prev_state.get("state") != curr_state.get("state"):
            transitions.append({
                "from_state": prev_state.get("state"),
                "to_state": curr_state.get("state"),
                "frame": curr_state.get("frame", 0),
                "timestamp": curr_state.get("frame", 0) / 30.0,
                "transition_type": "zoom",
                "duration": 0.4
            })
    
    return transitions

def _extract_face_tracking_info(layout_states: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract face tracking information from layout states"""
    face_info = {
        "total_faces_detected": 0,
        "primary_faces": [],
        "face_detection_frames": 0,
        "no_face_frames": 0,
        "speaking_scores": []
    }
    
    for state in layout_states:
        config = state.get("config", {})
        primary_face = config.get("primary_face")
        
        if primary_face:
            face_info["face_detection_frames"] += 1
            face_info["total_faces_detected"] = max(
                face_info["total_faces_detected"],
                config.get("face_tracks_count", 0)
            )
            
            if primary_face.get("track_id"):
                face_info["primary_faces"].append({
                    "track_id": primary_face["track_id"],
                    "bbox": primary_face["bbox"],
                    "speaking_score": primary_face.get("speaking_score", 0.0),
                    "frame": state.get("frame", 0)
                })
                
                if primary_face.get("speaking_score"):
                    face_info["speaking_scores"].append(primary_face["speaking_score"])
        else:
            face_info["no_face_frames"] += 1
    
    # Calculate average speaking score
    if face_info["speaking_scores"]:
        face_info["avg_speaking_score"] = sum(face_info["speaking_scores"]) / len(face_info["speaking_scores"])
    else:
        face_info["avg_speaking_score"] = 0.0
    
    return face_info

def _generate_transcript_file_list(transcript_info: Dict[str, Any], clip_id: str, output_dir: str) -> List[Dict[str, Any]]:
    """Generate list of transcript files for different formats"""
    transcript_files = []
    
    if not transcript_info.get("enabled", True):
        return transcript_files
    
    formats = ["srt", "vtt", "ass", "json"]
    
    for fmt in formats:
        filename = f"{clip_id}.{fmt}"
        filepath = os.path.join(output_dir, filename)
        
        transcript_files.append({
            "format": fmt,
            "filename": filename,
            "filepath": filepath
        })
    
    return transcript_files

def _assess_vertical_quality(layout_states: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Assess the quality of vertical rendering"""
    if not layout_states:
        return {"score": 0, "issues": ["No layout states available"]}
    
    # Count state distribution
    state_counts = {}
    for state in layout_states:
        state_name = state.get("state", "unknown")
        state_counts[state_name] = state_counts.get(state_name, 0) + 1
    
    # Quality scoring
    score = 100
    issues = []
    
    # Check if we have face-focused rendering
    vert_focus_frames = state_counts.get("vert_focus", 0)
    total_frames = len(layout_states)
    
    if vert_focus_frames > 0:
        face_ratio = vert_focus_frames / total_frames
        if face_ratio < 0.3:
            score -= 20
            issues.append("Low face-focused rendering ratio")
        elif face_ratio > 0.8:
            score -= 10
            issues.append("Very high face-focused ratio (may miss context)")
    else:
        score -= 30
        issues.append("No face-focused rendering detected")
    
    # Check for smooth transitions
    transitions = _extract_transitions(layout_states)
    if len(transitions) > total_frames * 0.1:  # More than 10% of frames have transitions
        score -= 15
        issues.append("Excessive state transitions")
    
    # Check for scene cuts
    scene_cuts = sum(1 for state in layout_states if state.get("config", {}).get("scene_cut_detected", False))
    if scene_cuts > 0:
        score -= 5
        issues.append(f"Scene cuts detected: {scene_cuts}")
    
    return {
        "score": max(0, score),
        "state_distribution": state_counts,
        "face_focus_ratio": vert_focus_frames / total_frames if total_frames > 0 else 0,
        "transitions_count": len(transitions),
        "scene_cuts": scene_cuts,
        "issues": issues
    }


def _get_file_size(file_path: str) -> Optional[int]:
    """Get file size in bytes"""
    try:
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
    except Exception:
        pass
    return None

def _calculate_file_hash(file_path: str) -> Optional[str]:
    """Calculate SHA-256 hash of file"""
    try:
        import hashlib
        if os.path.exists(file_path):
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
    except Exception:
        pass
    return None

def _verify_transcript_files(transcript_info: Dict[str, Any], clip_id: str, output_dir: str) -> List[Dict[str, Any]]:
    """Verify existence and integrity of transcript files"""
    verification_results = []
    
    if not transcript_info.get("enabled", True):
        return verification_results
    
    transcript_files = _generate_transcript_file_list(transcript_info, clip_id, output_dir)
    
    for transcript_file in transcript_files:
        filepath = transcript_file["filepath"]
        exists = os.path.exists(filepath)
        size = _get_file_size(filepath) if exists else None
        
        verification_results.append({
            "format": transcript_file["format"],
            "exists": exists,
            "file_size": size,
            "file_hash": _calculate_file_hash(filepath) if exists else None
        })
    
    return verification_results

def generate_batch_manifest(
    clips: List[Dict[str, Any]],
    output_dir: str = "outputs"
) -> str:
    """
    Generate a batch manifest for multiple clips.
    
    Args:
        clips: List of clip information dictionaries
        output_dir: Output directory for manifest
        
    Returns:
        Path to generated batch manifest file
    """
    
    batch_manifest = {
        "batch_id": f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_clips": len(clips),
        "output_directory": output_dir,
        "clips": []
    }
    
    # Add summary information for each clip
    for clip in clips:
        clip_summary = {
            "clip_id": clip.get("clip_id", "unknown"),
            "duration": clip.get("duration", 0),
            "output_path": clip.get("output_path", ""),
            "layout_mode": clip.get("layout_mode", "unknown"),
            "transcript_enabled": clip.get("transcript_enabled", True)
        }
        batch_manifest["clips"].append(clip_summary)
    
    # Generate batch manifest file
    batch_filename = f"batch_manifest_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    batch_path = os.path.join(output_dir, batch_filename)
    
    try:
        with open(batch_path, 'w', encoding='utf-8') as f:
            json.dump(batch_manifest, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Generated batch manifest: {batch_path}")
        return batch_path
        
    except Exception as e:
        print(f"❌ Failed to generate batch manifest: {e}")
        return ""
