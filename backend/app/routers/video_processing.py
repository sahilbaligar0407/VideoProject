from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form, Depends, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.requests import Request
import os
import uuid
import aiofiles
import subprocess
from typing import Optional
import asyncio
from datetime import datetime, timedelta
from app.services.video_processor import VideoProcessor
from app.services.auto_captions import CaptionStyle, WordStyle
from app.models import VideoProcessingResponse, ProcessingStatus
from app.settings import settings
from pydantic import BaseModel
from app.auth.dependencies import require_auth, get_optional_user
from app.db.saved_clips import get_user_saved_clips, get_saved_clip_by_clip_id
import json
import shutil
import glob

router = APIRouter()

# In-memory storage for processing status (in production, use Redis or database)
processing_status = {}


class CaptionConfigRequest(BaseModel):
    """Request model for caption configuration"""
    enabled: bool = True
    position: str = "bottom"
    regular_words: dict
    wow_words: dict
    like_words: dict

@router.post("/process-video")
async def process_video(
    background_tasks: BackgroundTasks,
    youtube_url: Optional[str] = Form(None),
    video_file: Optional[UploadFile] = File(None),
    user_topics: Optional[str] = Form(None),
    vertical: Optional[str] = Form("true"),
    caption_font_family: Optional[str] = Form(None),
    caption_font_size: Optional[str] = Form(None),
    caption_text_color: Optional[str] = Form(None),
    caption_stroke_color: Optional[str] = Form(None),
    current_user: dict = Depends(require_auth)  # Require authentication
):
    """Process video from either YouTube URL or file upload for viral clip generation - requires authentication"""
    try:
        user_id = current_user["id"]
        user_email = current_user.get("email", "unknown")
        print(f"🔐 Video processing request from user: {user_email} (ID: {user_id})")
    except Exception as e:
        print(f"❌ Error extracting user info from current_user: {e}")
        print(f"   current_user: {current_user}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error. Please sign in again.",
        )
    
    # Debug logging
    print(f"🔍 Received request:")
    print(f"  YouTube URL: {youtube_url}")
    print(f"  Video file: {video_file.filename if video_file else 'None'}")
    if video_file:
        try:
            # Try to get file size if available
            file_size = getattr(video_file, 'size', None)
            if file_size:
                print(f"  File size: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")
            else:
                print(f"  File size: Unknown (will be determined during upload)")
        except Exception as e:
            print(f"  File size: Could not determine ({e})")
    print(f"  User topics: {user_topics}")
    print(f"  Vertical output: {vertical}")
    
    if not youtube_url and not video_file:
        raise HTTPException(status_code=400, detail="Either YouTube URL or video file must be provided")
    
    if youtube_url and video_file:
        raise HTTPException(status_code=400, detail="Provide either YouTube URL OR video file, not both")
    
    # Validate file size if file is provided
    if video_file:
        # Note: FastAPI UploadFile.size might not always be available
        # We'll validate during the actual file read process
        pass
    
    # Parse parameters
    vertical_bool = vertical.lower() == "true" if vertical else True
    
    # Parse user topics if provided
    user_topics_list = None
    if user_topics:
        try:
            user_topics_list = [topic.strip() for topic in user_topics.split(",") if topic.strip()]
            print(f"🎯 Parsed user topics: {user_topics_list}")
        except Exception as e:
            print(f"⚠️ Failed to parse user topics: {e}")
            user_topics_list = None
    
    # Parse caption style if provided
    caption_style = None
    if caption_font_family or caption_font_size or caption_text_color:
        try:
            font_size = int(caption_font_size) if caption_font_size else 32
            text_color = caption_text_color if caption_text_color else "yellow"
            stroke_color = caption_stroke_color if caption_stroke_color else "black"
            font_family = caption_font_family if caption_font_family else "Arial"
            
            caption_style = CaptionStyle(
                font_family=font_family,
                font_size=font_size,
                text_color=text_color,
                stroke_color=stroke_color
            )
            print(f"🎨 Caption style: {font_family}, {font_size}px, {text_color} text, {stroke_color} stroke")
        except Exception as e:
            print(f"⚠️ Failed to parse caption style: {e}, using defaults")
            caption_style = None
    
    try:
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Initialize processing status (store user_id for cleanup and tracking)
        # Note: Processing won't start until caption config is saved (or skipped)
        processing_status[request_id] = {
            "status": "pending_caption_config",
            "progress": 0,
            "message": "Waiting for caption configuration...",
            "current_step": "initializing",
            "clips": None,
            "error": None,
            "user_topics": user_topics_list,
            "vertical": vertical_bool,
            "user_id": user_id,  # Store user_id for cleanup
            "created_at": datetime.utcnow().isoformat(),
            "caption_style": None,  # Will be set when user configures captions
            "youtube_url": youtube_url if youtube_url else None,  # Store for later processing
            "video_path": None  # Will be set for file uploads
        }
        
        # Don't start processing yet - wait for caption config
        # Processing will start when caption config is saved via /jobs/{request_id}/captions endpoint
        if youtube_url:
            print(f"📝 YouTube video submitted, waiting for caption config: {request_id}")
        else:
            print(f"📝 File uploaded, waiting for caption config: {request_id}")
            # Save the file first, then process it in the background
            # This allows the endpoint to return quickly
            try:
                # Ensure upload directory exists
                os.makedirs(settings.upload_dir, exist_ok=True)
                
                # Save the file immediately (this will complete the upload)
                video_path = os.path.join(settings.upload_dir, f"{request_id}_{video_file.filename}")
                print(f"💾 Saving uploaded file to: {video_path}")
                
                # Stream the file in chunks
                chunk_size = 1024 * 1024  # 1MB chunks
                total_written = 0
                
                async with aiofiles.open(video_path, 'wb') as f:
                    while True:
                        chunk = await video_file.read(chunk_size)
                        if not chunk:
                            break
                        await f.write(chunk)
                        total_written += len(chunk)
                        print(f"📥 Received {total_written / (1024*1024):.1f} MB")
                
                # Verify file was saved
                if os.path.exists(video_path):
                    actual_size = os.path.getsize(video_path)
                    print(f"✅ File saved successfully: {actual_size} bytes ({actual_size / (1024*1024):.2f} MB)")
                else:
                    raise Exception(f"File was not saved to {video_path}")
                
                # Don't start processing yet - wait for caption config
                # Store video path for later processing
                processing_status[request_id]["video_path"] = video_path
            except Exception as e:
                print(f"❌ Error saving uploaded file: {e}")
                import traceback
                traceback.print_exc()
                processing_status[request_id]["status"] = "failed"
                processing_status[request_id]["error"] = str(e)
                processing_status[request_id]["message"] = f"Failed to save uploaded file: {str(e)}"
                raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")
        
        return {
            "request_id": request_id,
            "status": "pending_caption_config",
            "message": "Video submitted. Please configure captions to continue.",
            "user_topics": user_topics_list,
            "vertical": vertical_bool
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in process_video endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process video request: {str(e)}")

@router.post("/jobs/{request_id}/captions")
async def save_caption_config(
    request_id: str,
    config: CaptionConfigRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_auth)
):
    """Save caption configuration for a job before processing starts"""
    if request_id not in processing_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Verify user owns this job
    if processing_status[request_id].get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Convert to CaptionStyle object
    # Note: When enabled=True, AutoCaptions uses hard-coded styling from the repository
    # The style parameters from frontend are ignored, but we still need to create a CaptionStyle object
    caption_style = CaptionStyle(
        enabled=config.enabled,
        position=config.position,  # Position may be used in future
        # Style parameters are ignored when using AutoCaptions (hard-coded styling)
        regular_words=WordStyle.from_dict(config.regular_words),
        wow_words=WordStyle.from_dict(config.wow_words),
        like_words=WordStyle.from_dict(config.like_words)
    )
    
    # Store caption config in processing status
    processing_status[request_id]["caption_style"] = caption_style.to_dict()
    
    if config.enabled:
        print(f"💾 Saved caption config for job {request_id}: enabled=True (using AutoCaptions hard-coded styling)")
    else:
        print(f"💾 Saved caption config for job {request_id}: enabled=False (no captions)")
    
    # Now start processing with the saved caption config
    job_data = processing_status[request_id]
    youtube_url = job_data.get("youtube_url")
    video_path = job_data.get("video_path")
    user_topics = job_data.get("user_topics")
    vertical = job_data.get("vertical")
    user_id = job_data.get("user_id")
    
    if youtube_url:
        print(f"🚀 Starting YouTube processing with caption config: {request_id}")
        background_tasks.add_task(process_youtube_video, request_id, youtube_url, user_topics, vertical, user_id, caption_style)
    elif video_path:
        print(f"🚀 Starting file processing with caption config: {request_id}")
        background_tasks.add_task(process_uploaded_video_from_path, request_id, video_path, user_topics, vertical, user_id, caption_style)
    else:
        print(f"⚠️ No video source found for job {request_id}")
        raise HTTPException(status_code=400, detail="No video source found")
    
    return {"message": "Caption configuration saved and processing started", "request_id": request_id}


@router.get("/status/{request_id}")
async def get_processing_status(request_id: str):
    """Get the current processing status for a request"""
    if request_id not in processing_status:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return processing_status[request_id]

@router.get("/thumbnail/{clip_id}")
async def get_thumbnail(clip_id: str):
    """Get thumbnail image for a clip"""
    print(f"🔍 Thumbnail request for clip_id: {clip_id}")
    
    # Find the clip in processing status
    thumbnail_path = None
    
    for request_id, status in processing_status.items():
        if status.get("clips"):
            for clip in status["clips"]:
                if clip.get("clip_id") == clip_id:
                    thumbnail_path = clip.get("thumbnail_path")
                    if thumbnail_path:
                        break
            if thumbnail_path:
                break
    
    if not thumbnail_path:
        raise HTTPException(status_code=404, detail=f"Thumbnail not found for clip {clip_id}")
    
    # Make path absolute if it's relative
    if not os.path.isabs(thumbnail_path):
        thumbnail_path = os.path.abspath(thumbnail_path)
    
    if not os.path.exists(thumbnail_path):
        # Try to find it in output directory
        from app.settings import settings
        output_dir = os.path.abspath(settings.output_dir)
        basename = os.path.basename(thumbnail_path)
        alt_path = os.path.join(output_dir, basename)
        if os.path.exists(alt_path):
            thumbnail_path = alt_path
        else:
            # Try searching for thumbnail by clip_id
            try:
                files = os.listdir(output_dir)
                for filename in files:
                    if clip_id in filename and filename.endswith('_thumb.jpg'):
                        thumbnail_path = os.path.join(output_dir, filename)
                        break
            except:
                pass
            
            if not os.path.exists(thumbnail_path):
                raise HTTPException(status_code=404, detail=f"Thumbnail file not found: {thumbnail_path}")
    
    return FileResponse(
        thumbnail_path,
        media_type="image/jpeg",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=3600",
        }
    )

@router.get("/preview/{clip_id}")
async def preview_clip(clip_id: str):
    """Preview a generated clip (streaming, no authentication required)"""
    print(f"🔍 Preview request for clip_id: {clip_id}")
    
    # Find the clip in processing status
    clip_path = None
    
    for request_id, status in processing_status.items():
        if status.get("clips"):
            for clip in status["clips"]:
                if clip.get("clip_id") == clip_id:
                    clip_path = clip.get("file_path")
                    if clip_path:
                        break
            if clip_path:
                break
    
    if not clip_path:
        raise HTTPException(status_code=404, detail=f"Clip {clip_id} not found")
    
    # Make path absolute if it's relative
    if not os.path.isabs(clip_path):
        clip_path = os.path.abspath(clip_path)
    
    if not os.path.exists(clip_path):
        # Try to find it in output directory
        from app.settings import settings
        output_dir = os.path.abspath(settings.output_dir)
        basename = os.path.basename(clip_path)
        alt_path = os.path.join(output_dir, basename)
        if os.path.exists(alt_path):
            clip_path = alt_path
        else:
            # Try searching for clip by clip_id
            try:
                files = os.listdir(output_dir)
                for filename in files:
                    if clip_id in filename and filename.endswith('.mp4'):
                        clip_path = os.path.join(output_dir, filename)
                        break
            except:
                pass
            
            if not os.path.exists(clip_path):
                raise HTTPException(status_code=404, detail=f"Clip file not found: {clip_path}")
    
    file_size = os.path.getsize(clip_path)
    
    return FileResponse(
        clip_path,
        media_type="video/mp4",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",
        }
    )

@router.options("/download/{clip_id}")
async def download_clip_options(clip_id: str):
    """Handle CORS preflight request for download endpoint"""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@router.options("/preview/{clip_id}")
async def preview_clip_options(clip_id: str):
    """Handle CORS preflight request for preview endpoint"""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@router.get("/download/{clip_id}")
async def download_clip(clip_id: str, current_user: dict = Depends(require_auth)):
    """Download a generated clip - requires authentication"""
    print(f"🔍 Download request for clip_id: {clip_id} by user: {current_user['email']}")
    
    # Find the clip in processing status
    clip_path = None
    clip_info = None
    
    for request_id, status in processing_status.items():
        if status.get("clips"):
            for clip in status["clips"]:
                if clip.get("clip_id") == clip_id:
                    clip_path = clip.get("file_path")
                    clip_info = clip
                    print(f"📁 Found clip in status for request {request_id}: {clip}")
                    break
            if clip_path:
                break
    
    if not clip_path:
        print(f"❌ Clip {clip_id} not found in processing status")
        print(f"📊 Available request IDs: {list(processing_status.keys())}")
        # Print all clips for debugging
        for request_id, status in processing_status.items():
            if status.get("clips"):
                print(f"  Request {request_id} has {len(status['clips'])} clips")
                for clip in status["clips"]:
                    print(f"    - Clip ID: {clip.get('clip_id')}, Path: {clip.get('file_path')}")
        raise HTTPException(status_code=404, detail=f"Clip {clip_id} not found in processing status")
    
    # Make path absolute if it's relative
    if not os.path.isabs(clip_path):
        # Try relative to current working directory
        abs_path = os.path.abspath(clip_path)
        if os.path.exists(abs_path):
            clip_path = abs_path
        else:
            # Try relative to output directory
            from app.settings import settings
            output_dir = os.path.abspath(settings.output_dir)
            abs_path = os.path.join(output_dir, os.path.basename(clip_path))
            if os.path.exists(abs_path):
                clip_path = abs_path
    
    print(f"📁 Resolved clip path: {clip_path}")
    print(f"📂 File exists: {os.path.exists(clip_path)}")
    
    # If file still doesn't exist, search for it
    if not os.path.exists(clip_path):
        print(f"⚠️ File not found at expected path, searching...")
        from app.settings import settings
        output_dir = os.path.abspath(settings.output_dir)
        print(f"🔍 Searching in output directory: {output_dir}")
        
        if os.path.exists(output_dir):
            # List all files in output directory
            try:
                files = os.listdir(output_dir)
                print(f"📂 Files in output directory ({len(files)} total): {files[:10]}...")  # Show first 10
                
                # Look for files that contain the clip_id
                for filename in files:
                    if clip_id in filename and filename.endswith('.mp4'):
                        found_path = os.path.join(output_dir, filename)
                        if os.path.exists(found_path):
                            clip_path = found_path
                            print(f"✅ Found matching file: {clip_path}")
                            break
            except Exception as e:
                print(f"❌ Error listing output directory: {e}")
        
        if not clip_path or not os.path.exists(clip_path):
            error_msg = f"Clip file not found on disk. Expected: {clip_path}"
            print(f"❌ {error_msg}")
            print(f"📊 Output directory exists: {os.path.exists(output_dir) if 'output_dir' in locals() else 'N/A'}")
            raise HTTPException(status_code=404, detail=error_msg)
    
    # Verify file is readable and get file size
    try:
        file_size = os.path.getsize(clip_path)
        print(f"✅ File found: {clip_path} ({file_size} bytes)")
    except Exception as e:
        print(f"❌ Error accessing file: {e}")
        raise HTTPException(status_code=500, detail=f"Error accessing clip file: {str(e)}")
    
    # Create file response with optimized headers for faster downloads
    # Note: FileResponse uses streaming, which is O(n) where n is file size - this is optimal
    # We enable range requests (Accept-Ranges: bytes) so browsers can:
    # 1. Resume interrupted downloads
    # 2. Stream video for preview (browsers request ranges for video playback)
    # 3. Show accurate download progress
    try:
        response = FileResponse(
            clip_path,
            media_type="video/mp4",
            filename=f"clip_{clip_id}.mp4",
            headers={
                "Content-Disposition": f'attachment; filename="clip_{clip_id}.mp4"',
                "Content-Length": str(file_size),  # Explicit content length for progress bars
                "Accept-Ranges": "bytes",  # Enable range requests for resumable downloads and video streaming
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS, HEAD",
                "Access-Control-Allow-Headers": "*",
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            }
        )
        
        print(f"✅ Returning file response for {clip_path} ({file_size} bytes)")
        return response
    except Exception as e:
        print(f"❌ Error creating file response: {e}")
        raise HTTPException(status_code=500, detail=f"Error serving clip file: {str(e)}")

@router.post("/topic-clips")
async def generate_topic_clips(
    background_tasks: BackgroundTasks,
    video_path: Optional[str] = Form(None),
    video_id: Optional[str] = Form(None),
    topics: str = Form(...),
    max_clips: Optional[int] = Form(5),
    vertical: Optional[str] = Form("true")
):
    """Generate clips based on specific topics from a video"""
    
    # Parse parameters
    vertical_bool = vertical.lower() == "true" if vertical else True
    
    # Parse topics
    try:
        topics_list = [topic.strip() for topic in topics.split(",") if topic.strip()]
        print(f"🎯 Topic-based clip generation requested for topics: {topics_list}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid topics format: {e}")
    
    if not topics_list:
        raise HTTPException(status_code=400, detail="At least one topic must be provided")
    
    # Validate video source
    if not video_path and not video_id:
        raise HTTPException(status_code=400, detail="Either video_path or video_id must be provided")
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Initialize processing status
    processing_status[request_id] = {
        "status": "processing",
        "progress": 0,
        "message": "Starting topic-based clip generation...",
        "current_step": "initializing",
        "clips": None,
        "error": None,
        "user_topics": topics_list,
        "vertical": vertical_bool,
        "max_clips": max_clips
    }
    
    # Start background processing
    background_tasks.add_task(
        process_topic_clips, 
        request_id, 
        video_path or video_id, 
        topics_list, 
        vertical_bool, 
        max_clips
    )
    
    return {
        "request_id": request_id,
        "status": "processing",
        "message": "Topic-based clip generation started",
        "topics": topics_list,
        "max_clips": max_clips,
        "vertical": vertical_bool
    }

@router.get("/clips/{request_id}/rankings")
async def get_clip_rankings(request_id: str):
    """Get detailed ranking information for generated clips"""
    if request_id not in processing_status:
        raise HTTPException(status_code=404, detail="Request not found")
    
    status = processing_status[request_id]
    if status["status"] != "completed":
        raise HTTPException(status_code=400, detail="Processing not completed yet")
    
    clips = status.get("clips", [])
    if not clips:
        raise HTTPException(status_code=404, detail="No clips found")
    
    # Extract ranking information
    rankings = []
    for clip in clips:
        if hasattr(clip, 'ranking') and clip.ranking:
            rankings.append({
                "clip_id": clip.clip_id,
                "start_time": clip.start_time,
                "end_time": clip.end_time,
                "duration": clip.duration,
                "viral_score": clip.ranking.viral_score,
                "engagement_potential": clip.ranking.engagement_potential,
                "shareability": clip.ranking.shareability,
                "trending_potential": clip.ranking.trending_potential,
                "ranking_factors": clip.ranking.ranking_factors,
                "face_tracking_applied": getattr(clip, 'face_tracking_applied', False),
                "speaker_centered": getattr(clip, 'speaker_centered', False)
            })
    
    # Calculate summary statistics
    if rankings:
        scores = [r["viral_score"] for r in rankings]
        summary = {
            "total_clips": len(rankings),
            "average_score": round(sum(scores) / len(scores), 2),
            "top_score": max(scores),
            "lowest_score": min(scores),
            "score_distribution": {
                "excellent": len([s for s in scores if s >= 4.5]),
                "very_good": len([s for s in scores if 4.0 <= s < 4.5]),
                "good": len([s for s in scores if 3.5 <= s < 4.0]),
                "average": len([s for s in scores if 3.0 <= s < 3.5]),
                "below_average": len([s for s in scores if 2.0 <= s < 3.0]),
                "poor": len([s for s in scores if 1.0 <= s < 2.0]),
                "very_poor": len([s for s in scores if s < 1.0])
            }
        }
    else:
        summary = {}
    
    return {
        "request_id": request_id,
        "rankings": rankings,
        "summary": summary
    }

async def process_youtube_video(request_id: str, youtube_url: str, user_topics: Optional[list], vertical: bool, user_id: int, caption_style: Optional[CaptionStyle] = None):
    """Process YouTube video with actual download and processing"""
    try:
        # Update status
        processing_status[request_id]["current_step"] = "downloading_youtube"
        processing_status[request_id]["message"] = "Downloading YouTube video..."
        processing_status[request_id]["progress"] = 10
        
        # Download YouTube video using yt-dlp
        video_path = await download_youtube_video(request_id, youtube_url)
        
        # Update status
        processing_status[request_id]["current_step"] = "processing_video"
        processing_status[request_id]["message"] = "Processing downloaded video..."
        processing_status[request_id]["progress"] = 30
        
        # Create status update callback
        def update_status(step: str, progress: int, message: str):
            """Update processing status during video processing"""
            processing_status[request_id]["current_step"] = step
            processing_status[request_id]["progress"] = progress
            processing_status[request_id]["message"] = message
        
        # Process the video with status updates
        processor = VideoProcessor(status_callback=update_status)
        clips = await processor.process_video(video_path, "youtube", user_topics, vertical, caption_style)
        
        print(f"Generated {len(clips)} clips from YouTube video")
        
        # Convert clips to dict for JSON serialization
        clips_dict = []
        for clip in clips:
            clip_dict = {
                "clip_id": clip.clip_id,
                "start_time": clip.start_time,
                "end_time": clip.end_time,
                "duration": clip.duration,
                "file_path": clip.file_path,
                "thumbnail_path": clip.thumbnail_path,
                "thumbnail_url": f"/api/v1/thumbnail/{clip.clip_id}" if clip.thumbnail_path else None,
                "preview_url": f"/api/v1/preview/{clip.clip_id}",  # Preview endpoint (no auth required)
                "caption_text": clip.caption_text,
                "download_url": f"/api/v1/download/{clip.clip_id}",  # Download endpoint (auth required)
                "ranking": clip.ranking.dict() if clip.ranking else None,
                "transcript_paths": clip.transcript_paths if hasattr(clip, 'transcript_paths') and clip.transcript_paths else []
            }
            clips_dict.append(clip_dict)
            print(f"Clip {clip.clip_id}: {clip.file_path}")
            print(f"  File exists: {os.path.exists(clip.file_path)}")
            if os.path.exists(clip.file_path):
                print(f"  File size: {os.path.getsize(clip.file_path)} bytes")
            if hasattr(clip, 'transcript_paths') and clip.transcript_paths:
                print(f"  Transcript files: {len(clip.transcript_paths)} files")
        
        # Update final status
        processing_status[request_id]["status"] = "completed"
        processing_status[request_id]["progress"] = 100
        processing_status[request_id]["message"] = "YouTube video processing completed successfully!"
        processing_status[request_id]["current_step"] = "completed"
        processing_status[request_id]["clips"] = clips_dict
        
        # Schedule cleanup of unsaved clips after 1 hour
        # This will delete clips and transcript files that are not saved to user's library
        asyncio.create_task(schedule_cleanup_unsaved_clips(request_id, user_id, clips_dict, delay_hours=1))
        
        print(f"Final clips in status: {clips_dict}")
        
        # Cleanup downloaded video
        try:
            os.remove(video_path)
        except:
            pass
            
    except Exception as e:
        processing_status[request_id]["status"] = "failed"
        processing_status[request_id]["error"] = str(e)
        processing_status[request_id]["message"] = f"Processing failed: {str(e)}"
        print(f"❌ YouTube processing failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Cleanup temp files even on failure
        try:
            from app.services.video_processor import VideoProcessor
            processor = VideoProcessor()
            processor._cleanup_temp_files()
        except:
            pass

async def download_youtube_video(request_id: str, youtube_url: str) -> str:
    """Download YouTube video using pytube (with yt-dlp fallback)"""
    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    # Try pytube first (simpler and more reliable for basic downloads)
    try:
        return await _download_with_pytube(request_id, youtube_url)
    except Exception as pytube_error:
        print(f"⚠️ pytube download failed: {pytube_error}")
        print("🔄 Falling back to yt-dlp...")
        try:
            return await _download_with_ytdlp(request_id, youtube_url)
        except Exception as ytdlp_error:
            print(f"❌ yt-dlp download also failed: {ytdlp_error}")
            raise Exception(f"YouTube download failed with both methods. pytube: {str(pytube_error)}, yt-dlp: {str(ytdlp_error)}")


async def _download_with_pytube(request_id: str, youtube_url: str) -> str:
    """Download YouTube video using pytube"""
    from pytube import YouTube
    from pytube.exceptions import VideoUnavailable, RegexMatchError
    
    # Create video path
    video_path = os.path.join(settings.upload_dir, f"{request_id}_youtube_video.mp4")
    
    print(f"📥 Downloading YouTube video with pytube: {youtube_url}")
    print(f"📁 Save path: {video_path}")
    
    # Run pytube in executor to avoid blocking
    def download_video():
        try:
            # Create YouTube object with bypass_age_gate=True to handle age-restricted videos
            yt = YouTube(youtube_url, use_oauth=False, allow_oauth_cache=True)
            
            # Get video title for logging (this might fail for some videos, so wrap in try-except)
            try:
                title = yt.title
                author = yt.author
                length = yt.length
                print(f"📹 Video title: {title}")
                print(f"👤 Channel: {author}")
                print(f"⏱️ Duration: {length} seconds")
            except Exception as info_error:
                print(f"⚠️ Could not get video info: {info_error}")
            
            # Get the best quality stream (720p or lower, progressive if available)
            # Try progressive first (video + audio in one file)
            streams = yt.streams
            
            # Try to get progressive streams first
            stream = streams.filter(
                progressive=True,
                file_extension='mp4',
                res='720p'
            ).first()
            
            # If no 720p progressive, try 480p
            if not stream:
                stream = streams.filter(
                    progressive=True,
                    file_extension='mp4',
                    res='480p'
                ).first()
            
            # If no 480p, try 360p
            if not stream:
                stream = streams.filter(
                    progressive=True,
                    file_extension='mp4',
                    res='360p'
                ).first()
            
            # If no progressive streams, get highest quality progressive available
            if not stream:
                stream = streams.filter(
                    progressive=True,
                    file_extension='mp4'
                ).order_by('resolution').desc().first()
            
            # If still no progressive, try any MP4 stream
            if not stream:
                stream = streams.filter(
                    file_extension='mp4'
                ).order_by('resolution').desc().first()
            
            # Last resort: get any available stream
            if not stream:
                stream = streams.get_highest_resolution()
            
            if not stream:
                available_streams = streams.all()
                raise Exception(f"No suitable video stream found. Available streams: {len(available_streams)}")
            
            print(f"📊 Selected stream: {stream.resolution if hasattr(stream, 'resolution') and stream.resolution else 'N/A'} ({stream.mime_type if hasattr(stream, 'mime_type') else 'unknown'})")
            if hasattr(stream, 'filesize') and stream.filesize:
                print(f"📦 File size: {stream.filesize / (1024*1024):.2f} MB")
            
            # Download to the specified path
            # pytube's download method returns the file path
            try:
                downloaded_file = stream.download(output_path=settings.upload_dir, filename=f"{request_id}_youtube_video.mp4")
                return downloaded_file if downloaded_file else video_path
            except Exception as download_error:
                # If download with filename fails, try without filename and rename later
                print(f"⚠️ Download with filename failed, trying without...")
                downloaded_file = stream.download(output_path=settings.upload_dir)
                # pytube might name it with the video title, so we need to find it
                if downloaded_file and os.path.exists(downloaded_file):
                    # Rename to our expected filename
                    import shutil
                    if downloaded_file != video_path:
                        shutil.move(downloaded_file, video_path)
                    return video_path
                else:
                    raise Exception(f"Download failed: {download_error}")
                
        except VideoUnavailable as e:
            raise Exception(f"Video is unavailable: {str(e)}")
        except RegexMatchError as e:
            raise Exception(f"Invalid YouTube URL or video format: {str(e)}")
        except Exception as e:
            raise Exception(f"pytube error: {str(e)}")
    
    # Run download in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    downloaded_path = await loop.run_in_executor(None, download_video)
    
    # Verify file was downloaded
    if not os.path.exists(downloaded_path):
        # pytube might have downloaded with a different name or extension
        upload_dir_files = os.listdir(settings.upload_dir)
        for filename in upload_dir_files:
            if filename.startswith(request_id) and (filename.endswith('.mp4') or filename.endswith('.webm')):
                downloaded_path = os.path.join(settings.upload_dir, filename)
                print(f"🔍 Found downloaded file: {downloaded_path}")
                break
        else:
            raise Exception(f"Video file was not downloaded. Expected: {video_path}")
    
    file_size = os.path.getsize(downloaded_path)
    print(f"✅ YouTube video downloaded: {downloaded_path} ({file_size / (1024*1024):.2f} MB)")
    
    return downloaded_path


async def _download_with_ytdlp(request_id: str, youtube_url: str) -> str:
    """Download YouTube video using yt-dlp (fallback method)"""
    import yt_dlp
    
    # Create base download path (yt-dlp will add extension)
    base_filename = f"{request_id}_youtube_video"
    video_path_template = os.path.join(settings.upload_dir, f"{base_filename}.%(ext)s")
    
    # Configure yt-dlp options with better headers to avoid 403 errors
    ydl_opts = {
        'format': 'best[height<=720]/bestvideo[height<=720]+bestaudio/best',  # Download 720p or lower
        'outtmpl': video_path_template,
        'merge_output_format': 'mp4',  # Merge to mp4 if separate video/audio
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
        'noplaylist': True,
        # Better user agent to avoid detection
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Add referer
        'referer': 'https://www.youtube.com/',
        # Retry configuration
        'retries': 3,
        'fragment_retries': 3,
        'file_access_retries': 3,
        # Extractor options for YouTube
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'web'],  # Try different clients
                'player_skip': ['webpage', 'configs'],  # Skip some steps that might fail
            }
        },
        # HTTP headers
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': 'https://www.youtube.com/',
        },
    }
    
    print(f"📥 Downloading YouTube video with yt-dlp: {youtube_url}")
    print(f"📁 Save path template: {video_path_template}")
    
    # Download video using yt-dlp Python module
    def download():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to see if it works
                info = ydl.extract_info(youtube_url, download=False)
                print(f"📹 Video title: {info.get('title', 'Unknown')}")
                print(f"👤 Channel: {info.get('uploader', 'Unknown')}")
                print(f"⏱️ Duration: {info.get('duration', 0)} seconds")
                
                # Now download
                ydl.download([youtube_url])
        except Exception as e:
            # If the above fails, try with simpler options
            print(f"⚠️ Standard download failed, trying simplified options...")
            simple_opts = {
                'format': 'worst[height<=720]/worst',  # Try worst quality first (less likely to be blocked)
                'outtmpl': video_path_template,
                'quiet': False,
                'no_warnings': False,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'referer': 'https://www.youtube.com/',
            }
            with yt_dlp.YoutubeDL(simple_opts) as ydl:
                ydl.download([youtube_url])
    
    # Run in executor to avoid blocking
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, download)
    
    # Find the downloaded file (yt-dlp adds extension)
    base_path = os.path.join(settings.upload_dir, base_filename)
    video_path = None
    for ext in ['.mp4', '.webm', '.mkv', '.m4a', '.mov', '.mp3']:
        potential_path = base_path + ext
        if os.path.exists(potential_path):
            video_path = potential_path
            break
    
    if not video_path:
        # Try to find any file starting with the base filename
        upload_dir_files = os.listdir(settings.upload_dir)
        for filename in upload_dir_files:
            if filename.startswith(base_filename):
                video_path = os.path.join(settings.upload_dir, filename)
                break
    
    if not video_path or not os.path.exists(video_path):
        raise Exception(f"Video file was not downloaded. Checked: {base_path}.*")
    
    file_size = os.path.getsize(video_path)
    print(f"✅ YouTube video downloaded: {video_path} ({file_size / (1024*1024):.2f} MB)")
    
    return video_path

async def process_uploaded_video_from_path(request_id: str, video_path: str, user_topics: Optional[list], vertical: bool, user_id: int, caption_style: Optional[CaptionStyle] = None):
    """Process uploaded video file from saved path"""
    try:
        # Get caption style from processing status if not provided
        if caption_style is None and request_id in processing_status:
            caption_config = processing_status[request_id].get("caption_style")
            if caption_config:
                caption_style = CaptionStyle.from_dict(caption_config)
            elif processing_status[request_id].get("status") == "pending_caption_config":
                # If no caption config and status is pending, use default (enabled)
                caption_style = CaptionStyle()
        
        # Validate file type
        file_extension = os.path.splitext(video_path)[1].lower()
        if file_extension not in settings.supported_formats:
            raise Exception(f"Unsupported file format: {file_extension}")
        
        # Update status to processing
        processing_status[request_id]["status"] = "processing"
        processing_status[request_id]["current_step"] = "processing_video"
        processing_status[request_id]["message"] = "Processing video..."
        processing_status[request_id]["progress"] = 20
        
        print(f"🎬 Starting video processing for: {video_path}")
        
        # Create status update callback
        def update_status(step: str, progress: int, message: str):
            """Update processing status during video processing"""
            processing_status[request_id]["current_step"] = step
            processing_status[request_id]["progress"] = progress
            processing_status[request_id]["message"] = message
        
        # Process the video with status updates
        processor = VideoProcessor(status_callback=update_status)
        clips = await processor.process_video(video_path, "file", user_topics, vertical, caption_style)
        
        print(f"Generated {len(clips)} clips")
        
        # Convert clips to dict for JSON serialization
        clips_dict = []
        for clip in clips:
            clip_dict = {
                "clip_id": clip.clip_id,
                "start_time": clip.start_time,
                "end_time": clip.end_time,
                "duration": clip.duration,
                "file_path": clip.file_path,
                "thumbnail_path": clip.thumbnail_path,
                "thumbnail_url": f"/api/v1/thumbnail/{clip.clip_id}" if clip.thumbnail_path else None,
                "preview_url": f"/api/v1/preview/{clip.clip_id}",  # Preview endpoint (no auth required)
                "caption_text": clip.caption_text,
                "download_url": f"/api/v1/download/{clip.clip_id}",  # Download endpoint (auth required)
                "ranking": clip.ranking.dict() if clip.ranking else None,
                "transcript_paths": clip.transcript_paths if hasattr(clip, 'transcript_paths') and clip.transcript_paths else []
            }
            clips_dict.append(clip_dict)
            print(f"Clip {clip.clip_id}: {clip.file_path}")
            print(f"  File exists: {os.path.exists(clip.file_path)}")
            if os.path.exists(clip.file_path):
                print(f"  File size: {os.path.getsize(clip.file_path)} bytes")
            if hasattr(clip, 'transcript_paths') and clip.transcript_paths:
                print(f"  Transcript files: {len(clip.transcript_paths)} files")
        
        # Update final status
        processing_status[request_id]["status"] = "completed"
        processing_status[request_id]["progress"] = 100
        processing_status[request_id]["message"] = "Video processing completed successfully!"
        processing_status[request_id]["current_step"] = "completed"
        processing_status[request_id]["clips"] = clips_dict
        
        # Schedule cleanup of unsaved clips after 1 hour
        # This will delete clips and transcript files that are not saved to user's library
        asyncio.create_task(schedule_cleanup_unsaved_clips(request_id, user_id, clips_dict, delay_hours=1))
        
        print(f"Final clips in status: {clips_dict}")
        
        # Cleanup uploaded file
        try:
            os.remove(video_path)
        except:
            pass
        
        # Cleanup temp files after successful processing
        try:
            from app.services.video_processor import VideoProcessor
            processor = VideoProcessor()
            processor._cleanup_temp_files()
        except:
            pass
            
    except Exception as e:
        processing_status[request_id]["status"] = "failed"
        processing_status[request_id]["error"] = str(e)
        processing_status[request_id]["message"] = f"Processing failed: {str(e)}"
        
        # Cleanup temp files even on failure
        try:
            from app.services.video_processor import VideoProcessor
            processor = VideoProcessor()
            processor._cleanup_temp_files()
        except:
            pass

async def simulate_processing_steps(request_id: str, input_type: str):
    """Simulate processing steps for YouTube videos (placeholder)"""
    steps = [
        ("transcribing", "Transcribing audio...", 30),
        ("detecting_highlights", "Detecting highlight segments...", 50),
        ("generating_clips", "Generating highlight clips...", 70),
        ("generating_transcripts", "Generating transcript files...", 90),
        ("completed", "Processing completed!", 100)
    ]
    
    for step, message, progress in steps:
        processing_status[request_id]["current_step"] = step
        processing_status[request_id]["message"] = message
        processing_status[request_id]["progress"] = progress
        await asyncio.sleep(1)
    
    # For YouTube, we'll create placeholder clips
    placeholder_clips = [
        {
            "clip_id": str(uuid.uuid4()),
            "start_time": 0,
            "end_time": 30,
            "duration": 30,
            "file_path": "placeholder_clip_1.mp4",
            "caption_text": "YouTube video highlight clip 1",
            "download_url": f"/api/v1/download/{uuid.uuid4()}"
        },
        {
            "clip_id": str(uuid.uuid4()),
            "start_time": 60,
            "end_time": 90,
            "duration": 30,
            "file_path": "placeholder_clip_2.mp4",
            "caption_text": "YouTube video highlight clip 2",
            "download_url": f"/api/v1/download/{uuid.uuid4()}"
        }
    ]
    
    processing_status[request_id]["clips"] = placeholder_clips
    processing_status[request_id]["status"] = "completed"

async def process_topic_clips(
    request_id: str, 
    video_source: str, 
    topics: list, 
    vertical: bool, 
    max_clips: int
):
    """Process topic-based clip generation"""
    try:
        # Update status
        processing_status[request_id]["current_step"] = "processing_topics"
        processing_status[request_id]["message"] = f"Generating clips for topics: {', '.join(topics)}"
        
        # Determine if this is a file path or needs to be found
        video_path = video_source
        if not os.path.exists(video_source):
            # Try to find video by ID in processing status
            for status in processing_status.values():
                if status.get("clips"):
                    for clip in status["clips"]:
                        if clip.get("clip_id") == video_source:
                            # Extract from the original video
                            video_path = clip.get("file_path", "").replace("_captioned.mp4", ".mp4")
                            break
        
        if not os.path.exists(video_path):
            raise Exception(f"Video not found: {video_source}")
        
        # Process the video with topic focus
        processor = VideoProcessor()
        clips = await processor.process_video(
            video_path, 
            "file", 
            topics, 
            vertical
        )
        
        # Limit to requested number of clips
        if len(clips) > max_clips:
            clips = clips[:max_clips]
            print(f"📊 Limited clips to {max_clips} as requested")
        
        # Convert clips to dict format
        clips_dict = [
            {
                "clip_id": clip.clip_id,
                "start_time": clip.start_time,
                "end_time": clip.end_time,
                "duration": clip.duration,
                "file_path": clip.file_path,
                "thumbnail_path": getattr(clip, 'thumbnail_path', None),
                "thumbnail_url": f"/api/v1/thumbnail/{clip.clip_id}" if getattr(clip, 'thumbnail_path', None) else None,
                "preview_url": f"/api/v1/preview/{clip.clip_id}",  # Preview endpoint (no auth required)
                "caption_text": clip.caption_text,
                "download_url": f"/api/v1/download/{clip.clip_id}",  # Download endpoint (auth required)
                "transcript_paths": getattr(clip, 'transcript_paths', None) or [],
                "ranking": getattr(clip, 'ranking', None).dict() if hasattr(clip, 'ranking') and getattr(clip, 'ranking', None) else None
            }
            for clip in clips
        ]
        
        # Update status
        processing_status[request_id]["status"] = "completed"
        processing_status[request_id]["progress"] = 100
        processing_status[request_id]["message"] = f"Generated {len(clips)} topic-based clips"
        processing_status[request_id]["clips"] = clips_dict
        
        # Get user_id from processing_status if available
        user_id = processing_status.get(request_id, {}).get("user_id")
        if user_id:
            # Schedule cleanup of unsaved clips after 1 hour
            asyncio.create_task(schedule_cleanup_unsaved_clips(request_id, user_id, clips_dict, delay_hours=1))
        
        print(f"✅ Topic-based clip generation completed: {len(clips)} clips")
        
    except Exception as e:
        print(f"❌ Topic-based clip generation failed: {e}")
        processing_status[request_id]["status"] = "failed"
        processing_status[request_id]["error"] = str(e)
        processing_status[request_id]["message"] = f"Topic-based clip generation failed: {str(e)}"


async def schedule_cleanup_unsaved_clips(request_id: str, user_id: int, clips_dict: list, delay_hours: int = 1):
    """Schedule cleanup of unsaved clips after a delay.
    
    This function waits for the specified delay, then checks which clips from the
    request have been saved to the user's library. Any clips that haven't been
    saved are deleted along with their transcript files and thumbnails.
    """
    await asyncio.sleep(delay_hours * 3600)  # Wait for delay_hours
    
    try:
        print(f"🧹 Starting cleanup of unsaved clips for request {request_id} (user {user_id})")
        
        # Get all saved clips for this user
        saved_clips = get_user_saved_clips(user_id)
        saved_clip_ids = {clip[2] for clip in saved_clips}  # clip_id is at index 2
        
        # Delete clips that are not saved
        deleted_count = 0
        for clip_data in clips_dict:
            clip_id = clip_data.get("clip_id")
            if clip_id in saved_clip_ids:
                print(f"  ✓ Skipping saved clip: {clip_id}")
                continue
            
            # Delete clip file
            file_path = clip_data.get("file_path")
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"  🗑️ Deleted clip file: {file_path}")
                    deleted_count += 1
                except Exception as e:
                    print(f"  ⚠️ Failed to delete clip file {file_path}: {e}")
            
            # Delete thumbnail
            thumbnail_path = clip_data.get("thumbnail_path")
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    os.remove(thumbnail_path)
                    print(f"  🗑️ Deleted thumbnail: {thumbnail_path}")
                except Exception as e:
                    print(f"  ⚠️ Failed to delete thumbnail {thumbnail_path}: {e}")
            
            # Delete transcript files
            transcript_paths = clip_data.get("transcript_paths", [])
            for transcript_path in transcript_paths:
                if transcript_path and os.path.exists(transcript_path):
                    try:
                        os.remove(transcript_path)
                        print(f"  🗑️ Deleted transcript file: {transcript_path}")
                    except Exception as e:
                        print(f"  ⚠️ Failed to delete transcript file {transcript_path}: {e}")
        
        print(f"✅ Cleanup completed: Deleted {deleted_count} unsaved clips")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
