"""
Authentication dependencies for FastAPI routes.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.users import get_user_by_id, is_user_banned
from app.auth.security import verify_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """Get current user from JWT token. Returns None if not authenticated."""
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        return None
    
    user_id_str = payload.get("sub")
    if not user_id_str:
        return None
    
    # Convert user_id from string to integer (JWT standard requires sub to be a string)
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        return None
    
    # Check if this is an admin (admin has user_id = -1)
    if user_id == -1:
        payload_admin = payload.get("admin", False)
        if payload_admin:
            return {
                "id": -1,
                "email": "admin",
                "created_at": "",
                "is_admin": True
            }
    
    user = get_user_by_id(user_id)
    if not user:
        return None
    
    # Check if user is banned (but don't raise error in optional auth)
    banned = user[4] if len(user) > 4 else 0
    if banned == 1:
        return None  # Banned users are treated as not authenticated
    
    return {
        "id": user[0],
        "email": user[1],
        "created_at": user[3],
        "is_admin": False
    }


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """Get current user from JWT token, but don't raise error if not authenticated."""
    return await get_current_user(credentials)


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """Require authentication - raises error if user is not authenticated."""
    if not credentials:
        print("❌ Authentication required: No credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    print(f"🔐 Verifying token: {token[:20]}...")
    payload = verify_token(token)
    
    if not payload:
        print(f"❌ Token verification failed: Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id_str = payload.get("sub")
    if not user_id_str:
        print(f"❌ Token validation failed: No user_id in payload. Payload: {payload}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Convert user_id from string to integer (JWT standard requires sub to be a string)
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        print(f"❌ Token validation failed: user_id is not a valid integer. user_id: {user_id_str}, type: {type(user_id_str)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if this is an admin (admin has user_id = -1)
    if user_id == -1:
        payload_admin = payload.get("admin", False)
        if payload_admin:
            print(f"✅ Admin token validated successfully")
            return {
                "id": -1,
                "email": "admin",
                "created_at": "",
                "is_admin": True
            }
    
    user = get_user_by_id(user_id)
    if not user:
        print(f"❌ Token validation failed: User not found. user_id: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is banned
    banned = user[4] if len(user) > 4 else 0
    if banned == 1:
        print(f"❌ User is banned: user_id: {user_id}, email: {user[1]}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are banned for violating TOS"
        )
    
    print(f"✅ Token validated successfully for user_id: {user_id}, email: {user[1]}")
    
    return {
        "id": user[0],
        "email": user[1],
        "created_at": user[3],
        "is_admin": False
    }

