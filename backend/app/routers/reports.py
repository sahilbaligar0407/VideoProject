"""
Reports router for users to submit reports.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Form, UploadFile, File
from typing import Optional
from app.auth.dependencies import require_auth
from app.db.reports import create_report
import json

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/clip")
async def report_clip(
    clip_id: str = Form(...),
    comment: Optional[str] = Form(None),
    current_user: dict = Depends(require_auth)
):
    """Report a clip for not being viral enough."""
    user_id = current_user["id"]
    
    report_id = create_report(
        user_id=user_id,
        report_type="clip_not_viral",
        clip_id=clip_id,
        comment=comment
    )
    
    if not report_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create report"
        )
    
    return {"message": "Report submitted successfully", "report_id": report_id}


@router.post("/error")
async def report_error(
    error_code: Optional[str] = Form(None),
    error_message: Optional[str] = Form(None),
    error_logs: Optional[str] = Form(None),
    comment: Optional[str] = Form(None),
    log_file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(require_auth)
):
    """Report an error in clip generation."""
    user_id = current_user["id"]
    
    # Read log file if provided
    logs_content = error_logs
    if log_file:
        try:
            logs_content = await log_file.read()
            logs_content = logs_content.decode('utf-8', errors='ignore')
            if error_logs:
                logs_content = error_logs + "\n\n--- Log File ---\n" + logs_content
        except Exception as e:
            print(f"Error reading log file: {e}")
            logs_content = error_logs or f"Error reading log file: {str(e)}"
    
    report_id = create_report(
        user_id=user_id,
        report_type="generation_error",
        error_code=error_code,
        error_message=error_message,
        error_logs=logs_content,
        comment=comment
    )
    
    if not report_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create report"
        )
    
    return {"message": "Error report submitted successfully", "report_id": report_id}

