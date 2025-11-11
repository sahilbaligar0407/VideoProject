"""
Database persistence for user authentication.
"""

import sqlite3
import os
from typing import Optional, Tuple
from datetime import datetime

def get_db_path() -> str:
    """Get the database file path."""
    db_dir = "app/db"
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "clipgenius.sqlite")


def init_users_db():
    """Initialize the users table in the database."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                banned INTEGER DEFAULT 0
            )
        """)
        
        # Add banned column if it doesn't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN banned INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            # Column already exists
            pass
        
        # Create index for email lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_banned ON users(banned)")
        
        conn.commit()


def create_user(email: str, password_hash: str) -> Optional[int]:
    """Create a new user in the database."""
    db_path = get_db_path()
    now = datetime.utcnow().isoformat()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (email, password_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (email.lower().strip(), password_hash, now, now))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        # Email already exists
        return None
    except Exception as e:
        print(f"Error creating user: {e}")
        return None


def get_user_by_email(email: str) -> Optional[Tuple[int, str, str, str, int]]:
    """Get user by email. Returns (id, email, password_hash, created_at, banned) or None."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, password_hash, created_at, COALESCE(banned, 0) as banned
            FROM users
            WHERE email = ?
        """, (email.lower().strip(),))
        
        result = cursor.fetchone()
        return result


def get_user_by_id(user_id: int) -> Optional[Tuple[int, str, str, str, int]]:
    """Get user by ID. Returns (id, email, password_hash, created_at, banned) or None."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, password_hash, created_at, COALESCE(banned, 0) as banned
            FROM users
            WHERE id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        return result


def update_user_password(user_id: int, password_hash: str) -> bool:
    """Update user password."""
    db_path = get_db_path()
    now = datetime.utcnow().isoformat()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users
                SET password_hash = ?, updated_at = ?
                WHERE id = ?
            """, (password_hash, now, user_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating user password: {e}")
        return False


def get_all_users() -> list:
    """Get all users. Returns list of (id, email, password_hash, created_at, banned)."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, password_hash, created_at, COALESCE(banned, 0) as banned
            FROM users
            ORDER BY created_at DESC
        """)
        
        return cursor.fetchall()


def ban_user(user_id: int) -> bool:
    """Ban a user by setting banned flag to 1."""
    db_path = get_db_path()
    now = datetime.utcnow().isoformat()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users
                SET banned = 1, updated_at = ?
                WHERE id = ?
            """, (now, user_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error banning user: {e}")
        return False


def unban_user(user_id: int) -> bool:
    """Unban a user by setting banned flag to 0."""
    db_path = get_db_path()
    now = datetime.utcnow().isoformat()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users
                SET banned = 0, updated_at = ?
                WHERE id = ?
            """, (now, user_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error unbanning user: {e}")
        return False


def is_user_banned(user_id: int) -> bool:
    """Check if a user is banned."""
    user = get_user_by_id(user_id)
    if user:
        return user[4] == 1  # banned is at index 4
    return False


def delete_user(user_id: int) -> bool:
    """Delete a user from the database.
    
    This will CASCADE delete all saved_clips for this user.
    Physical files (clips, thumbnails, transcripts) associated with saved clips
    are also deleted before the user record is removed.
    """
    db_path = get_db_path()
    import os
    import json
    
    try:
        # First, get all saved clips for this user to delete their files
        # We need to do this before deleting the user because CASCADE will remove the records
        saved_clips_list = []
        try:
            # Import here to avoid circular dependency issues
            from app.db.saved_clips import get_user_saved_clips
            saved_clips_list = get_user_saved_clips(user_id)
        except Exception as e:
            print(f"Warning: Could not fetch saved clips for deletion: {e}")
        
        # Delete physical files for saved clips
        for saved_clip in saved_clips_list:
            # saved_clip: (id, user_id, clip_id, file_path, thumbnail_path, transcript_paths, clip_metadata, created_at)
            file_path = saved_clip[3]
            thumbnail_path = saved_clip[4]
            transcript_paths_str = saved_clip[5]
            
            # Delete clip file
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Deleted clip file: {file_path}")
                except Exception as e:
                    print(f"Failed to delete clip file {file_path}: {e}")
            
            # Delete thumbnail
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    os.remove(thumbnail_path)
                    print(f"Deleted thumbnail: {thumbnail_path}")
                except Exception as e:
                    print(f"Failed to delete thumbnail {thumbnail_path}: {e}")
            
            # Delete transcript files
            if transcript_paths_str:
                try:
                    transcript_paths = json.loads(transcript_paths_str)
                    for transcript_path in transcript_paths:
                        if transcript_path and os.path.exists(transcript_path):
                            try:
                                os.remove(transcript_path)
                                print(f"Deleted transcript file: {transcript_path}")
                            except Exception as e:
                                print(f"Failed to delete transcript file {transcript_path}: {e}")
                except Exception as e:
                    print(f"Failed to parse transcript_paths: {e}")
        
        # Delete user (CASCADE will handle related records in saved_clips table)
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM users
                WHERE id = ?
            """, (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting user: {e}")
        import traceback
        traceback.print_exc()
        return False


# Initialize users table when module is imported
init_users_db()

