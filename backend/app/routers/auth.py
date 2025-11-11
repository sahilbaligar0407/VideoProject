"""
Authentication router for user signup and login.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models import UserSignup, UserLogin, TokenResponse, UserResponse
from app.db.users import create_user, get_user_by_email, get_user_by_id, is_user_banned
from app.auth.security import verify_password, get_password_hash, create_access_token, verify_token
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserSignup):
    """Create a new user account."""
    # Temporary predevelopment: Check early access code
    EARLY_ACCESS_CODE = "111"
    if user_data.early_access_code != EARLY_ACCESS_CODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid early access code. Please contact support for access."
        )
    
    # Check if user already exists
    existing_user = get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered. Please sign in instead."
        )
    
    # Validate password strength
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Hash password
    password_hash = get_password_hash(user_data.password)
    
    # Create user
    user_id = create_user(user_data.email, password_hash)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )
    
    # Get created user
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve created user"
        )
    
    # Create access token (sub must be a string for JWT standard)
    access_token = create_access_token(data={"sub": str(user_id)})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user[0],
            email=user[1],
            created_at=user[3]
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Authenticate user and return access token."""
    # Check for admin login (hardcoded)
    ADMIN_EMAIL = "admin"
    ADMIN_PASSWORD = "Popularmmos0407"
    
    if user_data.email.lower() == ADMIN_EMAIL and user_data.password == ADMIN_PASSWORD:
        # Admin login - create a special admin token
        # Use a negative user_id to distinguish admin from regular users
        admin_id = -1
        access_token = create_access_token(data={"sub": str(admin_id), "admin": True})
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=admin_id,
                email=ADMIN_EMAIL,
                created_at=datetime.utcnow().isoformat()
            )
        )
    
    # Regular user login
    user = get_user_by_email(user_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is banned
    banned = user[4] if len(user) > 4 else 0
    if banned == 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are banned for violating TOS"
        )
    
    # Verify password
    if not verify_password(user_data.password, user[2]):  # user[2] is password_hash
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token (sub must be a string for JWT standard)
    user_id = user[0]
    access_token = create_access_token(data={"sub": str(user_id)})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user[0],
            email=user[1],
            created_at=user[3]
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Get current user information from token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Convert user_id from string to integer (JWT standard requires sub to be a string)
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )
    
    # Check if this is an admin (admin has user_id = -1)
    if user_id == -1:
        payload_admin = payload.get("admin", False)
        if payload_admin:
            return UserResponse(
                id=-1,
                email="admin",
                created_at=datetime.utcnow().isoformat()
            )
    
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is banned
    banned = user[4] if len(user) > 4 else 0
    if banned == 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are banned for violating TOS"
        )
    
    return UserResponse(
        id=user[0],
        email=user[1],
        created_at=user[3]
    )

