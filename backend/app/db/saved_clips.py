"""
Database persistence for saved clips.
"""

import sqlite3
import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

def get_db_path() -> str:
    """Get the database file path."""
    db_dir = "app/db"
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "clipgenius.sqlite")


def init_saved_clips_db():
    """Initialize the saved_clips table in the database."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Create saved_clips table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_clips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                clip_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                thumbnail_path TEXT,
                transcript_paths TEXT,  -- JSON array of transcript file paths
                clip_metadata TEXT,     -- JSON object with clip info (start_time, end_time, duration, etc.)
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, clip_id)
            )
        """)
        
        # Create index for user lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_saved_clips_user_id ON saved_clips(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_saved_clips_clip_id ON saved_clips(clip_id)")
        
        conn.commit()


def get_user_saved_clips_count(user_id: int) -> int:
    """Get the number of clips saved by a user."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM saved_clips
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        return result[0] if result else 0


def save_clip(
    user_id: int,
    clip_id: str,
    file_path: str,
    thumbnail_path: Optional[str] = None,
    transcript_paths: Optional[List[str]] = None,
    clip_metadata: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """Save a clip to user's library. Returns saved_clip_id or None if limit exceeded."""
    db_path = get_db_path()
    
    # Check if user has reached the limit (3 clips)
    current_count = get_user_saved_clips_count(user_id)
    if current_count >= 3:
        return None
    
    # Check if clip is already saved
    existing = get_saved_clip_by_clip_id(user_id, clip_id)
    if existing:
        return existing[0]  # Return existing saved_clip_id
    
    now = datetime.utcnow().isoformat()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO saved_clips (user_id, clip_id, file_path, thumbnail_path, transcript_paths, clip_metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                clip_id,
                file_path,
                thumbnail_path,
                json.dumps(transcript_paths) if transcript_paths else None,
                json.dumps(clip_metadata) if clip_metadata else None,
                now
            ))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        # Clip already saved
        return None
    except Exception as e:
        print(f"Error saving clip: {e}")
        return None


def get_user_saved_clips(user_id: int) -> List[tuple]:
    """Get all saved clips for a user. Returns list of (id, user_id, clip_id, file_path, thumbnail_path, transcript_paths, clip_metadata, created_at)."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, clip_id, file_path, thumbnail_path, transcript_paths, clip_metadata, created_at
            FROM saved_clips
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        
        return cursor.fetchall()


def get_saved_clip_by_clip_id(user_id: int, clip_id: str) -> Optional[tuple]:
    """Get a saved clip by user_id and clip_id."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, clip_id, file_path, thumbnail_path, transcript_paths, clip_metadata, created_at
            FROM saved_clips
            WHERE user_id = ? AND clip_id = ?
        """, (user_id, clip_id))
        
        return cursor.fetchone()


def delete_saved_clip(user_id: int, clip_id: str) -> bool:
    """Delete a saved clip from user's library."""
    db_path = get_db_path()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM saved_clips
                WHERE user_id = ? AND clip_id = ?
            """, (user_id, clip_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting saved clip: {e}")
        return False


def get_saved_clip_by_id(saved_clip_id: int, user_id: int) -> Optional[tuple]:
    """Get a saved clip by saved_clip_id and user_id (for security)."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, clip_id, file_path, thumbnail_path, transcript_paths, clip_metadata, created_at
            FROM saved_clips
            WHERE id = ? AND user_id = ?
        """, (saved_clip_id, user_id))
        
        return cursor.fetchone()


# Initialize saved_clips table when module is imported
init_saved_clips_db()

