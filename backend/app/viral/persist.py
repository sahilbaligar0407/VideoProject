"""
Database persistence for viral similarity engine data.
"""

import sqlite3
import os
import pickle
import numpy as np
from typing import List, Optional, Tuple
from datetime import datetime

from ..config import settings


def get_db_path() -> str:
    """Get the database file path."""
    db_dir = "app/db"
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "clipgenius.sqlite")


def init_db():
    """Initialize the database with required tables."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Create viral_terms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS viral_terms (
                term TEXT PRIMARY KEY,
                weight REAL NOT NULL
            )
        """)
        
        # Create viral_vector table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS viral_vector (
                model TEXT PRIMARY KEY,
                vector BLOB NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Create video_embeddings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_embeddings (
                video_id TEXT NOT NULL,
                level TEXT NOT NULL,
                ref_start REAL NOT NULL,
                ref_end REAL NOT NULL,
                embedding BLOB NOT NULL,
                PRIMARY KEY (video_id, level, ref_start, ref_end)
            )
        """)
        
        # Create viral_scores table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS viral_scores (
                video_id TEXT NOT NULL,
                start REAL NOT NULL,
                end REAL NOT NULL,
                score REAL NOT NULL,
                PRIMARY KEY (video_id, start, end)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_viral_scores_video_id ON viral_scores(video_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_viral_scores_score ON viral_scores(score)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_embeddings_video_id ON video_embeddings(video_id)")
        
        conn.commit()


def upsert_viral_terms(terms: List[Tuple[str, float]]):
    """Insert or update viral terms in the database."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        for term, weight in terms:
            cursor.execute("""
                INSERT OR REPLACE INTO viral_terms (term, weight)
                VALUES (?, ?)
            """, (term, weight))
        
        conn.commit()


def get_viral_terms_from_db() -> List[Tuple[str, float]]:
    """Get all viral terms from the database."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT term, weight FROM viral_terms ORDER BY term")
        return cursor.fetchall()


def upsert_viral_vector(model: str, vector: np.ndarray, updated_at: str):
    """Insert or update viral vector in the database."""
    db_path = get_db_path()
    
    # Serialize numpy array to bytes
    vector_bytes = pickle.dumps(vector)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO viral_vector (model, vector, updated_at)
            VALUES (?, ?, ?)
        """, (model, vector_bytes, updated_at))
        conn.commit()


def get_viral_vector_from_db(model: str) -> Tuple[Optional[np.ndarray], Optional[str]]:
    """Get viral vector from the database."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT vector, updated_at FROM viral_vector 
            WHERE model = ?
        """, (model,))
        
        result = cursor.fetchone()
        if result:
            vector_bytes, updated_at = result
            vector = pickle.loads(vector_bytes)
            return vector, updated_at
        
        return None, None


def upsert_video_embeddings(video_id: str, level: str, ref_start: float, 
                           ref_end: float, embedding: np.ndarray):
    """Insert or update video embedding in the database."""
    db_path = get_db_path()
    
    # Serialize numpy array to bytes
    embedding_bytes = pickle.dumps(embedding)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO video_embeddings 
            (video_id, level, ref_start, ref_end, embedding)
            VALUES (?, ?, ?, ?, ?)
        """, (video_id, level, ref_start, ref_end, embedding_bytes))
        conn.commit()


def get_video_embeddings(video_id: str, level: str) -> List[Tuple[float, float, np.ndarray]]:
    """Get all embeddings for a video at a specific level."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ref_start, ref_end, embedding FROM video_embeddings
            WHERE video_id = ? AND level = ?
            ORDER BY ref_start
        """, (video_id, level))
        
        results = []
        for row in cursor.fetchall():
            ref_start, ref_end, embedding_bytes = row
            embedding = pickle.loads(embedding_bytes)
            results.append((ref_start, ref_end, embedding))
        
        return results


def upsert_viral_scores(video_id: str, scores: List[Tuple[float, float, float]]):
    """Insert or update viral scores in the database."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        for start, end, score in scores:
            cursor.execute("""
                INSERT OR REPLACE INTO viral_scores (video_id, start, end, score)
                VALUES (?, ?, ?, ?)
            """, (video_id, start, end, score))
        
        conn.commit()


def get_viral_scores(video_id: str, limit: int = 10) -> List[Tuple[float, float, float]]:
    """Get top viral scores for a video."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT start, end, score FROM viral_scores
            WHERE video_id = ?
            ORDER BY score DESC
            LIMIT ?
        """, (video_id, limit))
        
        return cursor.fetchall()


def delete_video_data(video_id: str):
    """Delete all data associated with a video."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Delete embeddings
        cursor.execute("DELETE FROM video_embeddings WHERE video_id = ?", (video_id,))
        
        # Delete scores
        cursor.execute("DELETE FROM viral_scores WHERE video_id = ?", (video_id,))
        
        conn.commit()


def get_database_stats() -> dict:
    """Get database statistics."""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Count viral terms
        cursor.execute("SELECT COUNT(*) FROM viral_terms")
        viral_terms_count = cursor.fetchone()[0]
        
        # Count viral vectors
        cursor.execute("SELECT COUNT(*) FROM viral_vector")
        viral_vectors_count = cursor.fetchone()[0]
        
        # Count video embeddings
        cursor.execute("SELECT COUNT(*) FROM video_embeddings")
        video_embeddings_count = cursor.fetchone()[0]
        
        # Count viral scores
        cursor.execute("SELECT COUNT(*) FROM viral_scores")
        viral_scores_count = cursor.fetchone()[0]
        
        return {
            "viral_terms": viral_terms_count,
            "viral_vectors": viral_vectors_count,
            "video_embeddings": video_embeddings_count,
            "viral_scores": viral_scores_count
        }


# Initialize database when module is imported
init_db()
