"""
Database persistence for user reports.
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


def init_reports_db():
    """Initialize the reports table in the database."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Create reports table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                report_type TEXT NOT NULL,
                clip_id TEXT,
                error_code TEXT,
                error_message TEXT,
                error_logs TEXT,
                comment TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at)")
        
        conn.commit()


def create_report(
    user_id: int,
    report_type: str,
    clip_id: Optional[str] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
    error_logs: Optional[str] = None,
    comment: Optional[str] = None
) -> Optional[int]:
    """Create a new report."""
    db_path = get_db_path()
    now = datetime.utcnow().isoformat()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reports (user_id, report_type, clip_id, error_code, error_message, error_logs, comment, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, report_type, clip_id, error_code, error_message, error_logs, comment, now))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Error creating report: {e}")
        return None


def get_all_reports() -> List[tuple]:
    """Get all reports. Returns list of (id, user_id, report_type, clip_id, error_code, error_message, error_logs, comment, created_at)."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, report_type, clip_id, error_code, error_message, error_logs, comment, created_at
            FROM reports
            ORDER BY created_at DESC
        """)
        
        return cursor.fetchall()


def get_reports_by_user(user_id: int) -> List[tuple]:
    """Get all reports for a specific user."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, report_type, clip_id, error_code, error_message, error_logs, comment, created_at
            FROM reports
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        
        return cursor.fetchall()


# Initialize reports table when module is imported
init_reports_db()

