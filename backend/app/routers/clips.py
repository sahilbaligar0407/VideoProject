"""
Enhanced clips router for ClipGenius Pipeline v2.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import FileResponse
from typing import List, Dict, Any, Optional
import os
import json
import uuid
from datetime import datetime

from app.config.features import PipelineConfig, get_default_config, load_config_from_dict
from app.prepass import track_faces, detect_speech_segments, detect_scene_changes
from app.layout.state_machine import LayoutStateMachine
from app.highlight.scoring import apply_enhanced_scoring
from app.captions import transcribe_audio, translate_captions
from app.ai_text import generate_titles_cta
from app.render import render_blur_background, render_gameplay_background
from app.services.video_processor import VideoProcessor
from app.settings import settings

router = APIRouter(prefix="/api/v1/clips", tags=["clips"])

# In-memory storage for processing status (replace with database in production)
processing_status = {}

@router.post("/generate")
async def generate_enhanced_clips(
    background_tasks: BackgroundTasks,
    video_file: UploadFile = File(...),
    config_json: str = Form("{}"),
    topics: Optional[str] = Form(None)
):
    """
    Generate enhanced clips using Pipeline v2
    
    Args:
        video_file: Video file to process
        config_json: JSON string with pipeline configuration
        topics: Comma-separated topics for content analysis
    """
    try:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Parse configuration
        try:
            config_dict = json.loads(config_json) if config_json else {}
            config = load_config_from_dict(config_dict)
        except Exception as e:
            print(f"⚠️ Config parsing failed, using defaults: {e}")
            config = get_default_config()
        
        # Validate configuration
        warnings = config.validate_config(config)
        if warnings:
            print(f"⚠️ Config warnings: {warnings}")
        
        # Save uploaded file
        file_path = os.path.join(settings.upload_dir, f"{request_id}_{video_file.filename}")
        with open(file_path, "wb") as f:
            content = await video_file.read()
            f.write(content)
        
        # Initialize processing status
        processing_status[request_id] = {
            "status": "processing",
            "progress": 0,
            "message": "Starting enhanced pipeline...",
            "created_at": datetime.now().isoformat(),
            "config": config.dict()
        }
        
        # Start background processing
        background_tasks.add_task(
            process_enhanced_pipeline,
            request_id,
            file_path,
            config,
            topics
        )
        
        return {
            "request_id": request_id,
            "status": "processing",
            "message": "Enhanced pipeline started",
            "config_summary": config.get_config_summary()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")

@router.get("/status/{request_id}")
async def get_processing_status(request_id: str):
    """Get processing status for a request"""
    if request_id not in processing_status:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return processing_status[request_id]

@router.get("/download/{request_id}/{clip_index}")
async def download_clip(request_id: str, clip_index: int):
    """Download a generated clip"""
    if request_id not in processing_status:
        raise HTTPException(status_code=404, detail="Request not found")
    
    status = processing_status[request_id]
    if status["status"] != "completed":
        raise HTTPException(status_code=400, detail="Processing not completed")
    
    if "clips" not in status or clip_index >= len(status["clips"]):
        raise HTTPException(status_code=404, detail="Clip not found")
    
    clip_path = status["clips"][clip_index]["video_path"]
    
    if not os.path.exists(clip_path):
        raise HTTPException(status_code=404, detail="Clip file not found")
    
    return FileResponse(
        clip_path,
        media_type="video/mp4",
        filename=f"clip_{clip_index + 1}.mp4"
    )

async def process_enhanced_pipeline(
    request_id: str,
    video_path: str,
    config: PipelineConfig,
    topics: Optional[str]
):
    """Process video through enhanced pipeline v2"""
    try:
        status = processing_status[request_id]
        
        # Step 1: Prepass detection
        status["message"] = "Running prepass detection..."
        status["progress"] = 10
        
        # Face tracking
        if config.face_tracking.enabled:
            status["message"] = "Tracking faces..."
            face_boxes = track_faces(video_path, sample_rate=10)
            print(f"✅ Face tracking complete: {len(face_boxes)} detections")
        else:
            face_boxes = []
        
        # Scene change detection
        if config.enable_scene_detection:
            status["message"] = "Detecting scene changes..."
            scene_changes = detect_scene_changes(video_path)
            print(f"✅ Scene detection complete: {len(scene_changes)} changes")
        else:
            scene_changes = []
        
        status["progress"] = 25
        
        # Step 2: Transcription and speech analysis
        status["message"] = "Transcribing audio..."
        
        # Extract audio for transcription
        video_processor = VideoProcessor()
        audio_path = await video_processor._extract_audio(video_path)
        
        # Transcribe with language detection
        transcription = transcribe_audio(
            audio_path,
            language=config.captions.language,
            translate_to="en" if config.captions.language != "en" else None
        )
        
        # Extract speech segments
        speech_segments = detect_speech_segments(transcription)
        print(f"✅ Transcription complete: {len(speech_segments)} speech segments")
        
        status["progress"] = 40
        
        # Step 3: Layout state machine
        status["message"] = "Computing layout states..."
        
        if face_boxes:
            # Initialize state machine for layout analysis
            state_machine = LayoutStateMachine(
                face_confidence_threshold=config.face_tracking.confidence_threshold,
                state_debounce_frames=config.face_tracking.debounce_frames,
                min_face_size=config.face_tracking.min_face_size,
                scene_cut_threshold=config.face_tracking.scene_cut_threshold
            )
            
            # Update speech segments for speaking score computation
            state_machine.update_speech_segments(speech_segments)
            
            # For now, create a simplified layout state representation
            # In a full implementation, you would process frames through the state machine
            layout_states = []
            for face_box in face_boxes:
                layout_states.append({
                    "timestamp": face_box.t,
                    "state": "vert_focus" if face_box.conf > config.face_tracking.confidence_threshold else "bg_blur_rect",
                    "face_confidence": face_box.conf,
                    "face_bbox": face_box.bbox
                })
            
            print(f"✅ Layout states computed: {len(layout_states)} states")
        else:
            layout_states = []
        
        status["progress"] = 55
        
        # Step 4: Enhanced highlight detection
        status["message"] = "Detecting highlights with enhanced scoring..."
        
        # Use existing video processor for highlight detection
        highlights = await video_processor._detect_highlights(video_path, transcription)
        
        # Apply enhanced scoring
        enhanced_highlights = apply_enhanced_scoring(
            highlights, face_boxes, speech_segments, scene_changes
        )
        
        print(f"✅ Enhanced highlights detected: {len(enhanced_highlights)} segments")
        
        status["progress"] = 70
        
        # Step 5: Generate clips
        status["message"] = "Generating enhanced clips..."
        
        clips = []
        for i, highlight in enumerate(enhanced_highlights[:config.video.num_clips]):
            try:
                # Determine layout mode
                if (config.face_tracking.enabled and 
                    has_face_focus_in_range(layout_states, highlight.start_time, highlight.end_time)):
                    layout_mode = "face_focus"
                else:
                    layout_mode = "blur_background"
                
                # Generate clip
                clip_result = await generate_enhanced_clip(
                    video_path, highlight, layout_mode, config, face_boxes, speech_segments
                )
                
                clips.append(clip_result)
                print(f"✅ Clip {i+1} generated: {clip_result['video_path']}")
                
            except Exception as e:
                print(f"⚠️ Failed to generate clip {i+1}: {e}")
                continue
        
        status["progress"] = 90
        
        # Step 6: AI text generation
        if config.ai.auto_titles and clips:
            status["message"] = "Generating AI titles and CTAs..."
            
            for clip in clips:
                try:
                    # Generate AI content
                    ai_content = generate_titles_cta(
                        clip["transcript"],
                        topics=topics.split(",") if topics else None
                    )
                    clip["ai_content"] = ai_content
                except Exception as e:
                    print(f"⚠️ AI content generation failed: {e}")
                    clip["ai_content"] = None
        
        status["progress"] = 100
        status["status"] = "completed"
        status["message"] = "Enhanced pipeline complete"
        status["clips"] = clips
        status["completed_at"] = datetime.now().isoformat()
        
        print(f"✅ Enhanced pipeline complete: {len(clips)} clips generated")
        
    except Exception as e:
        print(f"❌ Enhanced pipeline failed: {e}")
        processing_status[request_id]["status"] = "failed"
        processing_status[request_id]["message"] = f"Pipeline failed: {str(e)}"
        processing_status[request_id]["error"] = str(e)

async def generate_enhanced_clip(
    video_path: str,
    highlight,
    layout_mode: str,
    config: PipelineConfig,
    face_boxes: List,
    speech_segments: List
) -> Dict[str, Any]:
    """Generate a single enhanced clip"""
    
    # Create output path
    clip_id = str(uuid.uuid4())[:8]
    output_path = os.path.join(
        settings.output_dir,
        f"enhanced_clip_{clip_id}.mp4"
    )
    
    # Extract clip timing
    start_time = highlight.start_time
    duration = highlight.duration
    
    # Generate clip based on layout mode
    if layout_mode == "face_focus" and face_boxes:
        # Face-focused auto-reframe
        success = await generate_face_focus_clip(
            video_path, output_path, start_time, duration, face_boxes, config
        )
    else:
        # Blur background or gameplay background
        if config.background.mode == "gameplay" and config.background.game:
            success = await generate_gameplay_clip(
                video_path, output_path, start_time, duration, config
            )
        else:
            success = render_blur_background(
                video_path, output_path, start_time, duration
            )
    
    if not success:
        raise Exception("Clip generation failed")
    
    # Extract transcript for this clip
    clip_transcript = extract_clip_transcript(
        speech_segments, start_time, duration
    )
    
    return {
        "video_path": output_path,
        "start_time": start_time,
        "duration": duration,
        "layout_mode": layout_mode,
        "transcript": clip_transcript,
        "confidence_score": highlight.confidence_score
    }

async def generate_face_focus_clip(
    video_path: str,
    output_path: str,
    start_time: float,
    duration: float,
    face_boxes: List,
    config: PipelineConfig
) -> bool:
    """Generate face-focused clip with auto-reframe"""
    # This would implement the auto-reframe logic
    # For now, fall back to blur background
    return render_blur_background(
        video_path, output_path, start_time, duration
    )

async def generate_gameplay_clip(
    video_path: str,
    output_path: str,
    start_time: float,
    duration: float,
    config: PipelineConfig
) -> bool:
    """Generate gameplay background clip"""
    # This would implement the gameplay background logic
    # For now, fall back to blur background
    return render_blur_background(
        video_path, output_path, start_time, duration
    )

def extract_clip_transcript(
    speech_segments: List,
    start_time: float,
    duration: float
) -> str:
    """Extract transcript text for a specific clip"""
    clip_segments = []
    
    for segment in speech_segments:
        if (segment.start <= start_time + duration and 
            segment.end >= start_time):
            clip_segments.append(segment.text)
    
    return " ".join(clip_segments)

def has_face_focus_in_range(layout_states: List, start_time: float, end_time: float) -> bool:
    """Check if there's face focus in a time range"""
    for state in layout_states:
        if (start_time <= state["timestamp"] <= end_time and 
            state["state"] == "vert_focus"):  # VERT_FOCUS
            return True
    return False
