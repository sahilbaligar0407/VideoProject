from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.requests import Request
import os
import uuid
import aiofiles
import subprocess
from typing import Optional
import asyncio
from app.services.video_processor import VideoProcessor
from app.models import VideoProcessingResponse, ProcessingStatus
from app.settings import settings
import json

router = APIRouter()

# In-memory storage for processing status (in production, use Redis or database)
processing_status = {}

@router.post("/process-video")
async def process_video(
    background_tasks: BackgroundTasks,
    youtube_url: Optional[str] = Form(None),
    video_file: Optional[UploadFile] = File(None),
    user_topics: Optional[str] = Form(None),
    vertical: Optional[str] = Form("true")
):
    """Process video from either YouTube URL or file upload for viral clip generation"""
    
    # Debug logging
    print(f"🔍 Received request:")
    print(f"  YouTube URL: {youtube_url}")
    print(f"  Video file: {video_file.filename if video_file else 'None'}")
    print(f"  File size: {video_file.size if video_file else 'N/A'}")
    print(f"  User topics: {user_topics}")
    print(f"  Vertical output: {vertical}")
    
    if not youtube_url and not video_file:
        raise HTTPException(status_code=400, detail="Either YouTube URL or video file must be provided")
    
    if youtube_url and video_file:
        raise HTTPException(status_code=400, detail="Provide either YouTube URL OR video file, not both")
    
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
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Initialize processing status
    processing_status[request_id] = {
        "status": "processing",
        "progress": 0,
        "message": "Starting viral clip generation...",
        "current_step": "initializing",
        "clips": None,
        "error": None,
        "user_topics": user_topics_list,
        "vertical": vertical_bool
    }
    
    # Start background processing
    if youtube_url:
        print(f"🚀 Starting YouTube processing for request: {request_id}")
        background_tasks.add_task(process_youtube_video, request_id, youtube_url, user_topics_list, vertical_bool)
    else:
        print(f"🚀 Starting file upload processing for request: {request_id}")
        background_tasks.add_task(process_uploaded_video, request_id, video_file, user_topics_list, vertical_bool)
    
    return {
        "request_id": request_id,
        "status": "processing",
        "message": "Viral clip generation started",
        "user_topics": user_topics_list,
        "vertical": vertical_bool
    }

@router.get("/status/{request_id}")
async def get_processing_status(request_id: str):
    """Get the current processing status for a request"""
    if request_id not in processing_status:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return processing_status[request_id]

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

@router.get("/download/{clip_id}")
async def download_clip(clip_id: str):
    """Download a generated clip"""
    print(f"🔍 Download request for clip_id: {clip_id}")
    
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
    
    # Verify file is readable
    try:
        file_size = os.path.getsize(clip_path)
        print(f"✅ File found: {clip_path} ({file_size} bytes)")
    except Exception as e:
        print(f"❌ Error accessing file: {e}")
        raise HTTPException(status_code=500, detail=f"Error accessing clip file: {str(e)}")
    
    # Create file response with proper headers
    try:
        response = FileResponse(
            clip_path,
            media_type="video/mp4",
            filename=f"clip_{clip_id}.mp4",
            headers={
                "Content-Disposition": f'attachment; filename="clip_{clip_id}.mp4"',
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
        print(f"✅ Returning file response for {clip_path}")
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

async def process_youtube_video(request_id: str, youtube_url: str, user_topics: Optional[list], vertical: bool):
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
        
        # Process the downloaded video
        processor = VideoProcessor()
        clips = await processor.process_video(video_path, "youtube", user_topics, vertical)
        
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
                "caption_text": clip.caption_text,
                "download_url": clip.download_url
            }
            clips_dict.append(clip_dict)
            print(f"Clip {clip.clip_id}: {clip.file_path}")
            print(f"  File exists: {os.path.exists(clip.file_path)}")
            if os.path.exists(clip.file_path):
                print(f"  File size: {os.path.getsize(clip.file_path)} bytes")
        
        # Update final status
        processing_status[request_id]["status"] = "completed"
        processing_status[request_id]["progress"] = 100
        processing_status[request_id]["message"] = "YouTube video processing completed successfully!"
        processing_status[request_id]["current_step"] = "completed"
        processing_status[request_id]["clips"] = clips_dict
        
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

async def download_youtube_video(request_id: str, youtube_url: str) -> str:
    """Download YouTube video using yt-dlp"""
    try:
        # Create download path
        video_path = os.path.join(settings.upload_dir, f"{request_id}_youtube_video.mp4")
        
        # Use yt-dlp to download video
        cmd = [
            "yt-dlp",
            "-f", "best[height<=720]",  # Download 720p or lower for faster processing
            "-o", video_path,
            youtube_url
        ]
        
        print(f"📥 Downloading YouTube video: {youtube_url}")
        print(f"📁 Save path: {video_path}")
        print(f"🔧 Command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"YouTube download failed: {result.stderr}")
        
        if not os.path.exists(video_path):
            raise Exception("Video file was not downloaded")
        
        file_size = os.path.getsize(video_path)
        print(f"✅ YouTube video downloaded: {file_size} bytes")
        
        return video_path
        
    except Exception as e:
        print(f"❌ YouTube download failed: {e}")
        raise Exception(f"YouTube download failed: {str(e)}")

async def process_uploaded_video(request_id: str, video_file: UploadFile, user_topics: Optional[list], vertical: bool):
    """Process uploaded video file"""
    try:
        # Update status
        processing_status[request_id]["current_step"] = "saving_file"
        processing_status[request_id]["message"] = "Saving uploaded video..."
        processing_status[request_id]["progress"] = 10
        
        # Validate file type
        file_extension = os.path.splitext(video_file.filename)[1].lower()
        if file_extension not in settings.supported_formats:
            raise Exception(f"Unsupported file format: {file_extension}")
        
        # Save uploaded file
        video_path = os.path.join(settings.upload_dir, f"{request_id}_{video_file.filename}")
        print(f"💾 Saving uploaded file to: {video_path}")
        print(f"📁 Upload directory exists: {os.path.exists(settings.upload_dir)}")
        print(f"📄 File name: {video_file.filename}")
        print(f"📏 File size: {video_file.size} bytes")
        
        async with aiofiles.open(video_path, 'wb') as f:
            content = await video_file.read()
            await f.write(content)
        
        # Verify file was saved
        if os.path.exists(video_path):
            actual_size = os.path.getsize(video_path)
            print(f"✅ File saved successfully: {actual_size} bytes")
        else:
            raise Exception(f"File was not saved to {video_path}")
        
        # Update status
        processing_status[request_id]["current_step"] = "processing_video"
        processing_status[request_id]["message"] = "Processing video..."
        processing_status[request_id]["progress"] = 20
        
        # Process the video
        processor = VideoProcessor()
        clips = await processor.process_video(video_path, "file", user_topics, vertical)
        
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
                "caption_text": clip.caption_text,
                "download_url": clip.download_url
            }
            clips_dict.append(clip_dict)
            print(f"Clip {clip.clip_id}: {clip.file_path}")
            print(f"  File exists: {os.path.exists(clip.file_path)}")
            if os.path.exists(clip.file_path):
                print(f"  File size: {os.path.getsize(clip.file_path)} bytes")
        
        # Update final status
        processing_status[request_id]["status"] = "completed"
        processing_status[request_id]["progress"] = 100
        processing_status[request_id]["message"] = "Video processing completed successfully!"
        processing_status[request_id]["current_step"] = "completed"
        processing_status[request_id]["clips"] = clips_dict
        
        print(f"Final clips in status: {clips_dict}")
        
        # Cleanup uploaded file
        try:
            os.remove(video_path)
        except:
            pass
            
    except Exception as e:
        processing_status[request_id]["status"] = "failed"
        processing_status[request_id]["error"] = str(e)
        processing_status[request_id]["message"] = f"Processing failed: {str(e)}"

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
        
        # Update status
        processing_status[request_id]["status"] = "completed"
        processing_status[request_id]["progress"] = 100
        processing_status[request_id]["message"] = f"Generated {len(clips)} topic-based clips"
        processing_status[request_id]["clips"] = [
            {
                "clip_id": clip.clip_id,
                "start_time": clip.start_time,
                "end_time": clip.end_time,
                "duration": clip.duration,
                "file_path": clip.file_path,
                "caption_text": clip.caption_text,
                "download_url": clip.download_url
            }
            for clip in clips
        ]
        
        print(f"✅ Topic-based clip generation completed: {len(clips)} clips")
        
    except Exception as e:
        print(f"❌ Topic-based clip generation failed: {e}")
        processing_status[request_id]["status"] = "failed"
        processing_status[request_id]["error"] = str(e)
        processing_status[request_id]["message"] = f"Topic-based clip generation failed: {str(e)}"
