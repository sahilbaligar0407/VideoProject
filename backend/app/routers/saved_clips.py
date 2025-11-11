"""
Saved clips router for managing user's saved clips library.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any
from app.auth.dependencies import require_auth
from app.db.saved_clips import (
    save_clip,
    get_user_saved_clips,
    delete_saved_clip,
    get_user_saved_clips_count,
    get_saved_clip_by_clip_id
)
from app.models import SavedClipResponse, SaveClipRequest
import os
import json

router = APIRouter(prefix="/saved-clips", tags=["saved-clips"])


@router.get("", response_model=List[SavedClipResponse])
async def get_saved_clips(current_user: dict = Depends(require_auth)):
    """Get all saved clips for the current user."""
    try:
        user_id = current_user["id"]
        user_email = current_user.get("email", "unknown")
        print(f"📚 Getting saved clips for user: {user_email} (ID: {user_id})")
        
        saved_clips = get_user_saved_clips(user_id)
        print(f"   Found {len(saved_clips)} saved clips in database")
        
        clips_list = []
        for saved_clip in saved_clips:
            # saved_clip: (id, user_id, clip_id, file_path, thumbnail_path, transcript_paths, clip_metadata, created_at)
            saved_clip_id = saved_clip[0]
            clip_id = saved_clip[2]
            file_path = saved_clip[3]
            thumbnail_path = saved_clip[4]
            transcript_paths_str = saved_clip[5]
            clip_metadata_str = saved_clip[6]
            created_at = saved_clip[7]
            
            # Parse JSON strings
            try:
                transcript_paths = json.loads(transcript_paths_str) if transcript_paths_str else []
            except:
                transcript_paths = []
            
            try:
                clip_metadata = json.loads(clip_metadata_str) if clip_metadata_str else {}
            except:
                clip_metadata = {}
            
            # Verify file exists
            if not os.path.exists(file_path):
                print(f"   ⚠️ Skipping clip {clip_id}: file not found at {file_path}")
                # Skip clips where file doesn't exist
                continue
            
            clips_list.append({
                "id": saved_clip_id,
                "clip_id": clip_id,
                "file_path": file_path,
                "thumbnail_path": thumbnail_path,
                "thumbnail_url": f"/api/v1/thumbnail/{clip_id}" if thumbnail_path else None,
                "preview_url": f"/api/v1/preview/{clip_id}",
                "download_url": f"/api/v1/download/{clip_id}",
                "transcript_paths": transcript_paths,
                "clip_metadata": clip_metadata,
                "created_at": created_at
            })
        
        print(f"   Returning {len(clips_list)} valid saved clips")
        return clips_list
    except Exception as e:
        print(f"❌ Error getting saved clips: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get saved clips: {str(e)}"
        )


@router.post("", response_model=SavedClipResponse, status_code=status.HTTP_201_CREATED)
async def save_clip_to_library(
    request: SaveClipRequest,
    current_user: dict = Depends(require_auth)
):
    """Save a clip to user's library. Maximum 3 clips per user."""
    user_id = current_user["id"]
    
    # Check if user has reached the limit
    current_count = get_user_saved_clips_count(user_id)
    if current_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have reached the maximum limit of 3 saved clips. Please remove a clip before saving a new one."
        )
    
    # Check if clip is already saved
    existing = get_saved_clip_by_clip_id(user_id, request.clip_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This clip is already saved to your library."
        )
    
    # Verify clip file exists
    if not os.path.exists(request.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clip file not found. It may have been deleted."
        )
    
    # Save the clip
    saved_clip_id = save_clip(
        user_id=user_id,
        clip_id=request.clip_id,
        file_path=request.file_path,
        thumbnail_path=request.thumbnail_path,
        transcript_paths=request.transcript_paths,
        clip_metadata=request.clip_metadata
    )
    
    if not saved_clip_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to save clip. You may have reached the limit of 3 saved clips."
        )
    
    # Return the saved clip
    saved_clip = get_saved_clip_by_clip_id(user_id, request.clip_id)
    if not saved_clip:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve saved clip"
        )
    
    # Parse JSON strings
    transcript_paths = json.loads(saved_clip[5]) if saved_clip[5] else []
    clip_metadata = json.loads(saved_clip[6]) if saved_clip[6] else {}
    
    return {
        "id": saved_clip[0],
        "clip_id": saved_clip[2],
        "file_path": saved_clip[3],
        "thumbnail_path": saved_clip[4],
        "thumbnail_url": f"/api/v1/thumbnail/{saved_clip[2]}" if saved_clip[4] else None,
        "preview_url": f"/api/v1/preview/{saved_clip[2]}",
        "download_url": f"/api/v1/download/{saved_clip[2]}",
        "transcript_paths": transcript_paths,
        "clip_metadata": clip_metadata,
        "created_at": saved_clip[7]
    }


@router.delete("/{clip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_saved_clip(
    clip_id: str,
    current_user: dict = Depends(require_auth)
):
    """Remove a clip from user's saved clips library."""
    user_id = current_user["id"]
    
    success = delete_saved_clip(user_id, clip_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clip not found in your saved clips library"
        )
    
    return None


@router.get("/count")
async def get_saved_clips_count(current_user: dict = Depends(require_auth)):
    """Get the number of saved clips for the current user."""
    user_id = current_user["id"]
    count = get_user_saved_clips_count(user_id)
    
    return {
        "count": count,
        "max_clips": 3,
        "remaining": max(0, 3 - count)
    }

