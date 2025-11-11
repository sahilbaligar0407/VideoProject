"""
Admin router for managing users and reports.
"""

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from typing import Optional, List
from app.auth.dependencies import require_auth
from app.db.users import get_all_users, ban_user, unban_user, get_user_by_id, delete_user
from app.db.reports import get_all_reports, create_report
from app.models import UserResponse
import json

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(current_user: dict = Depends(require_auth)) -> dict:
    """Require admin authentication."""
    is_admin = current_user.get("is_admin", False) or current_user.get("id") == -1
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/users")
async def get_all_users_endpoint(admin: dict = Depends(require_admin)):
    """Get all users (admin only)."""
    users = get_all_users()
    
    users_list = []
    for user in users:
        # user: (id, email, password_hash, created_at, banned)
        users_list.append({
            "id": user[0],
            "email": user[1],
            "password_hash": user[2],  # Note: This is the hashed password, not the plain password
            "created_at": user[3],
            "banned": bool(user[4])
        })
    
    return {"users": users_list}


@router.post("/users/{user_id}/ban")
async def ban_user_endpoint(user_id: int, admin: dict = Depends(require_admin)):
    """Ban a user (admin only)."""
    if user_id == -1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot ban admin user"
        )
    
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = ban_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ban user"
        )
    
    return {"message": f"User {user[1]} has been banned", "user_id": user_id, "banned": True}


@router.post("/users/{user_id}/unban")
async def unban_user_endpoint(user_id: int, admin: dict = Depends(require_admin)):
    """Unban a user (admin only)."""
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = unban_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unban user"
        )
    
    return {"message": f"User {user[1]} has been unbanned", "user_id": user_id, "banned": False}


@router.get("/reports")
async def get_all_reports_endpoint(admin: dict = Depends(require_admin)):
    """Get all reports (admin only)."""
    reports = get_all_reports()
    
    reports_list = []
    for report in reports:
        # report: (id, user_id, report_type, clip_id, error_code, error_message, error_logs, comment, created_at)
        reports_list.append({
            "id": report[0],
            "user_id": report[1],
            "report_type": report[2],
            "clip_id": report[3],
            "error_code": report[4],
            "error_message": report[5],
            "error_logs": report[6],
            "comment": report[7],
            "created_at": report[8]
        })
    
    return {"reports": reports_list}


@router.delete("/users/{user_id}")
async def delete_user_endpoint(user_id: int, admin: dict = Depends(require_admin)):
    """Delete a user (admin only)."""
    if user_id == -1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete admin user"
        )
    
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
    
    return {"message": f"User {user[1]} has been deleted", "user_id": user_id}


@router.get("/me")
async def get_admin_info(admin: dict = Depends(require_admin)):
    """Get admin information."""
    return {
        "id": admin["id"],
        "email": admin["email"],
        "is_admin": True
    }

