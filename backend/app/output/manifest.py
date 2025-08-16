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
    caption_info: Dict[str, Any],
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
        caption_info: Caption generation information
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
        
        # Caption information
        "captions": {
            "enabled": caption_info.get("enabled", True),
            "mode": caption_info.get("mode", "sidecar"),
            "style": caption_info.get("style", "boxed_high_contrast"),
            "theme": caption_info.get("theme", "default"),
            "languages": caption_info.get("languages", ["en"]),
            "burn_in_language": caption_info.get("burn_in_language", "en"),
            "files": _generate_caption_file_list(caption_info, clip_id, output_dir)
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
            "caption_quality": _assess_caption_quality(caption_info),
            "overall_score": _calculate_overall_quality(layout_states, caption_info)
        },
        
        # File integrity
        "integrity": {
            "video_file_size": _get_file_size(output_path),
            "video_file_hash": _calculate_file_hash(output_path),
            "caption_files": _verify_caption_files(caption_info, clip_id, output_dir)
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

def _generate_caption_file_list(caption_info: Dict[str, Any], clip_id: str, output_dir: str) -> List[Dict[str, Any]]:
    """Generate list of caption files for different languages and formats"""
    caption_files = []
    
    if not caption_info.get("enabled", True):
        return caption_files
    
    languages = caption_info.get("languages", ["en"])
    formats = ["srt", "vtt", "ass", "json"]
    
    for lang in languages:
        for fmt in formats:
            filename = f"{clip_id}_captions_{lang}.{fmt}"
            filepath = os.path.join(output_dir, filename)
            
            caption_files.append({
                "language": lang,
                "format": fmt,
                "filename": filename,
                "filepath": filepath,
                "burn_in": lang == caption_info.get("burn_in_language", "en")
            })
    
    return caption_files

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

def _assess_caption_quality(caption_info: Dict[str, Any]) -> Dict[str, Any]:
    """Assess the quality of caption generation"""
    score = 100
    issues = []
    
    if not caption_info.get("enabled", True):
        return {"score": 0, "issues": ["Captions disabled"]}
    
    # Check caption mode
    mode = caption_info.get("mode", "sidecar")
    if mode == "burn":
        score += 10  # Bonus for burn-in
    elif mode == "off":
        score -= 50
        issues.append("Captions turned off")
    
    # Check style
    style = caption_info.get("style", "boxed_high_contrast")
    if style in ["boxed_high_contrast", "outline_bold"]:
        score += 5  # Bonus for high-quality styles
    
    # Check languages
    languages = caption_info.get("languages", ["en"])
    if len(languages) > 1:
        score += 15  # Bonus for multi-language support
    
    # Check burn-in language
    burn_lang = caption_info.get("burn_in_language", "en")
    if burn_lang in languages:
        score += 5
    else:
        score -= 10
        issues.append("Burn-in language not in supported languages")
    
    return {
        "score": max(0, score),
        "mode": mode,
        "style": style,
        "languages_count": len(languages),
        "burn_in_language": burn_lang,
        "issues": issues
    }

def _calculate_overall_quality(layout_states: List[Dict[str, Any]], caption_info: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate overall quality score for the clip"""
    layout_quality = _assess_vertical_quality(layout_states)
    caption_quality = _assess_caption_quality(caption_info)
    
    # Weighted scoring: 70% layout, 30% captions
    overall_score = (layout_quality["score"] * 0.7) + (caption_quality["score"] * 0.3)
    
    # Determine quality level
    if overall_score >= 90:
        quality_level = "excellent"
    elif overall_score >= 75:
        quality_level = "good"
    elif overall_score >= 60:
        quality_level = "fair"
    elif overall_score >= 40:
        quality_level = "poor"
    else:
        quality_level = "very_poor"
    
    return {
        "score": round(overall_score, 1),
        "level": quality_level,
        "layout_score": layout_quality["score"],
        "caption_score": caption_quality["score"],
        "recommendations": _generate_quality_recommendations(layout_quality, caption_quality)
    }

def _generate_quality_recommendations(layout_quality: Dict[str, Any], caption_quality: Dict[str, Any]) -> List[str]:
    """Generate quality improvement recommendations"""
    recommendations = []
    
    # Layout recommendations
    if layout_quality["score"] < 80:
        if "Low face-focused rendering ratio" in layout_quality["issues"]:
            recommendations.append("Improve face detection sensitivity or lighting")
        if "Excessive state transitions" in layout_quality["issues"]:
            recommendations.append("Increase state transition debounce frames")
        if "Scene cuts detected" in layout_quality["issues"]:
            recommendations.append("Review source video for abrupt scene changes")
    
    # Caption recommendations
    if caption_quality["score"] < 80:
        if "Captions turned off" in caption_quality["issues"]:
            recommendations.append("Enable captions for better accessibility")
        if "Burn-in language not in supported languages" in caption_quality["issues"]:
            recommendations.append("Ensure burn-in language is in supported languages list")
    
    if not recommendations:
        recommendations.append("Clip quality is excellent - no improvements needed")
    
    return recommendations

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

def _verify_caption_files(caption_info: Dict[str, Any], clip_id: str, output_dir: str) -> List[Dict[str, Any]]:
    """Verify existence and integrity of caption files"""
    verification_results = []
    
    if not caption_info.get("enabled", True):
        return verification_results
    
    caption_files = _generate_caption_file_list(caption_info, clip_id, output_dir)
    
    for caption_file in caption_files:
        filepath = caption_file["filepath"]
        exists = os.path.exists(filepath)
        size = _get_file_size(filepath) if exists else None
        
        verification_results.append({
            "language": caption_file["language"],
            "format": caption_file["format"],
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
            "caption_enabled": clip.get("caption_enabled", True),
            "languages": clip.get("languages", ["en"])
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
