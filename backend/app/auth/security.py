"""
Security utilities for authentication.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

# Import settings to ensure .env file is loaded by pydantic-settings
# This makes JWT_SECRET_KEY available via os.getenv()
from app.settings import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Module-level SECRET_KEY (will be read when needed)
SECRET_KEY = None

def get_secret_key() -> str:
    """Get the JWT secret key, ensuring it's loaded from environment.
    
    This function always reads from os.getenv() to ensure we get the latest value
    from the .env file, which is loaded by settings.py via load_dotenv().
    """
    global SECRET_KEY
    # Always read from environment (settings.py loads .env via load_dotenv())
    secret_key = os.getenv("JWT_SECRET_KEY")
    if not secret_key:
        # Fall back to default (should not happen in production)
        secret_key = "your-secret-key-change-in-production-min-32-chars"
        import warnings
        warnings.warn(
            "JWT_SECRET_KEY is not set in .env file. Using default (INSECURE - change in production).",
            UserWarning
        )
    
    # Cache it for logging purposes
    if SECRET_KEY is None:
        SECRET_KEY = secret_key
        # Log SECRET_KEY info at first load (for debugging, but don't log the actual key)
        print(f"🔑 JWT SECRET_KEY loaded: length={len(SECRET_KEY)}, first_10_chars={SECRET_KEY[:10]}...")
        if len(SECRET_KEY) < 32:
            import warnings
            warnings.warn(
                f"JWT_SECRET_KEY is too short (length: {len(SECRET_KEY)}). Please set a strong secret key in your .env file (minimum 32 characters).",
                UserWarning
            )
    
    return secret_key


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    # Get SECRET_KEY using the helper function
    secret_key = get_secret_key()
    
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    print(f"🔑 Creating token with data: {to_encode}")
    print(f"   SECRET_KEY length: {len(secret_key) if secret_key else 0}")
    print(f"   SECRET_KEY (first 10 chars): {secret_key[:10] if secret_key else 'None'}...")
    print(f"   Expires at: {expire} (UTC)")
    print(f"   Current time: {datetime.utcnow()} (UTC)")
    
    try:
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
        # jose library returns a string, but let's make sure
        if isinstance(encoded_jwt, bytes):
            encoded_jwt = encoded_jwt.decode('utf-8')
        print(f"   ✅ Token created successfully: {encoded_jwt[:50]}...")
        return encoded_jwt
    except Exception as e:
        print(f"   ❌ Error creating token: {e}")
        import traceback
        traceback.print_exc()
        raise


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token."""
    # Get SECRET_KEY using the helper function (same as creation)
    secret_key = get_secret_key()
    
    try:
        print(f"🔐 Verifying token with SECRET_KEY length: {len(secret_key) if secret_key else 0}")
        print(f"   SECRET_KEY (first 10 chars): {secret_key[:10] if secret_key else 'None'}...")
        print(f"   Token (first 50 chars): {token[:50]}...")
        print(f"   Current time: {datetime.utcnow()} (UTC)")
        
        # Verify the token
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        print(f"✅ Token decoded successfully. Payload: {payload}")
        if 'exp' in payload:
            exp_time = datetime.fromtimestamp(payload['exp'])
            print(f"   Expiration: {exp_time} (UTC)")
            print(f"   Time until expiration: {exp_time - datetime.utcnow()}")
        return payload
    except JWTError as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"❌ JWT Error during token verification: {error_type}: {error_msg}")
        print(f"   SECRET_KEY length: {len(secret_key) if secret_key else 0}")
        print(f"   SECRET_KEY (first 10 chars): {secret_key[:10] if secret_key else 'None'}...")
        print(f"   Token (first 50 chars): {token[:50]}...")
        
        # Try to decode without verification to see what's in the token
        try:
            import base64
            import json
            # JWT has 3 parts separated by dots
            parts = token.split('.')
            if len(parts) >= 2:
                # Decode the payload (second part) without verification
                payload_part = parts[1]
                # Add padding if needed
                payload_part += '=' * (4 - len(payload_part) % 4)
                decoded_payload = base64.urlsafe_b64decode(payload_part)
                token_data = json.loads(decoded_payload)
                print(f"   📋 Token payload (decoded without verification): {token_data}")
                if 'exp' in token_data:
                    exp_time = datetime.fromtimestamp(token_data['exp'])
                    current_time = datetime.utcnow()
                    print(f"   ⏰ Token expiration: {exp_time} (UTC)")
                    print(f"   ⏰ Current time: {current_time} (UTC)")
                    is_expired = current_time > exp_time
                    print(f"   ⚠️ Is expired: {is_expired}")
                    if is_expired:
                        time_since_exp = current_time - exp_time
                        print(f"   ⏱️ Expired {time_since_exp} ago")
        except Exception as decode_error:
            print(f"   ⚠️ Could not decode token payload: {decode_error}")
        
        return None
    except Exception as e:
        print(f"❌ Unexpected error during token verification: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def get_user_id_from_token(token: str) -> Optional[int]:
    """Extract user ID from a JWT token."""
    payload = verify_token(token)
    if payload:
        user_id_str = payload.get("sub")  # 'sub' is the user ID as a string
        if user_id_str:
            try:
                return int(user_id_str)  # Convert to integer
            except (ValueError, TypeError):
                return None
    return None

