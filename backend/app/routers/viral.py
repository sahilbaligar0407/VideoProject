"""
FastAPI routes for the Viral Similarity Engine.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import uuid

from ..models import (
    ViralTerm, ScoredWindow, ViralScoringRequest, ViralScoringResponse,
    ViralTermsResponse, ViralVectorResponse
)
from ..viral import (
    get_viral_terms, add_viral_term, update_viral_term, remove_viral_term,
    get_viral_vector, rebuild_viral_vector, window_captions,
    score_windows_against_viral_vector, filter_windows_by_score,
    create_highlight_segments_from_windows, upsert_viral_scores,
    get_viral_scores, upsert_video_embeddings, get_database_stats
)
from ..settings import settings

router = APIRouter(prefix="/api/v1/viral", tags=["viral"])


@router.post("/terms", response_model=Dict[str, Any])
async def add_or_update_viral_term(term: ViralTerm):
    """Add or update a viral term."""
    try:
        # Try to update first
        if update_viral_term(term.term, term.weight):
            return {"success": True, "action": "updated", "term": term.term}
        
        # If update failed, try to add
        if add_viral_term(term.term, term.weight):
            return {"success": True, "action": "added", "term": term.term}
        
        # If both failed, term might already exist or limit reached
        existing_terms = get_viral_terms()
        if len(existing_terms) >= settings.viral_max_terms:
            raise HTTPException(
                status_code=400, 
                detail=f"Maximum number of viral terms ({settings.viral_max_terms}) reached"
            )
        
        raise HTTPException(
            status_code=400, 
            detail="Failed to add or update viral term"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/terms", response_model=ViralTermsResponse)
async def list_viral_terms():
    """List all viral terms."""
    try:
        terms = get_viral_terms()
        return ViralTermsResponse(
            terms=terms,
            total_count=len(terms),
            max_terms=settings.viral_max_terms
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/terms/{term}")
async def delete_viral_term(term: str):
    """Delete a viral term."""
    try:
        if remove_viral_term(term):
            return {"success": True, "message": f"Term '{term}' deleted"}
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"Term '{term}' not found"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rebuild", response_model=ViralVectorResponse)
async def rebuild_viral_vector_endpoint():
    """Rebuild the viral vector from current terms."""
    try:
        result = await rebuild_viral_vector()
        return ViralVectorResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/videos/{video_id}/score-viral", response_model=ViralScoringResponse)
async def score_video_viral(video_id: str, request: ViralScoringRequest):
    """Score video captions against viral vector."""
    try:
        # Create windows from captions
        windows = window_captions(
            segments=request.captions,
            start=0,
            end=request.video_duration,
            window_sec=settings.viral_window_sec,
            hop_sec=settings.viral_window_hop
        )
        
        if not windows:
            return ViralScoringResponse(
                video_id=video_id,
                scored_windows=[],
                total_windows=0,
                viral_vector_info={"model": settings.embedding_model}
            )
        
        # Score windows against viral vector
        scored_windows = await score_windows_against_viral_vector(windows)
        
        # Filter by minimum score and keep top K
        top_windows = filter_windows_by_score(
            scored_windows, 
            settings.viral_min_score, 
            settings.viral_top_k
        )
        
        # Store scores in database
        scores_data = [(w.start_time, w.end_time, w.score) for w in top_windows]
        upsert_viral_scores(video_id, scores_data)
        
        # Store window embeddings for future use
        for window in top_windows:
            # Get embedding for this window text
            from ..viral.embeddings import embed_texts
            embeddings = await embed_texts([window.text])
            if embeddings and embeddings[0] is not None:
                upsert_video_embeddings(
                    video_id, "window", window.start_time, window.end_time, embeddings[0]
                )
        
        # Get viral vector info
        viral_vector, updated_at = await get_viral_vector()
        viral_vector_info = {
            "model": settings.embedding_model,
            "dimension": len(viral_vector) if viral_vector is not None else 0,
            "updated_at": updated_at
        }
        
        return ViralScoringResponse(
            video_id=video_id,
            scored_windows=top_windows,
            total_windows=len(windows),
            viral_vector_info=viral_vector_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos/{video_id}/viral-top")
async def get_video_viral_top(video_id: str, k: int = 5):
    """Get top viral scores for a video."""
    try:
        scores = get_viral_scores(video_id, limit=k)
        
        # Convert to ScoredWindow format
        scored_windows = []
        for start, end, score in scores:
            scored_window = ScoredWindow(
                start_time=start,
                end_time=end,
                score=score,
                text=f"Viral segment {start:.1f}s - {end:.1f}s"
            )
            scored_windows.append(scored_window)
        
        return {
            "video_id": video_id,
            "scored_windows": scored_windows,
            "total_found": len(scored_windows)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_viral_stats():
    """Get database statistics for the viral engine."""
    try:
        stats = get_database_stats()
        return {
            "database_stats": stats,
            "settings": {
                "embedding_model": settings.embedding_model,
                "viral_window_sec": settings.viral_window_sec,
                "viral_window_hop": settings.viral_window_hop,
                "viral_min_score": settings.viral_min_score,
                "viral_top_k": settings.viral_top_k,
                "viral_max_terms": settings.viral_max_terms
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_viral_engine():
    """Test endpoint to verify viral engine is working."""
    try:
        # Test viral vector computation
        viral_vector, updated_at = await get_viral_vector()
        
        # Test terms loading
        terms = get_viral_terms()
        
        return {
            "status": "working",
            "viral_vector": {
                "exists": viral_vector is not None,
                "dimension": len(viral_vector) if viral_vector is not None else 0,
                "updated_at": updated_at
            },
            "terms": {
                "count": len(terms),
                "sample": [t.term for t in terms[:5]] if terms else []
            },
            "embedding_model": settings.embedding_model
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
