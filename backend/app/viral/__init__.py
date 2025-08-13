"""
Viral Similarity Engine for ClipGenius

This module provides viral content detection using OpenAI embeddings and cosine similarity.
"""

from .embeddings import embed_texts, EmbeddingCache
from .viral_terms import ViralTerm, ViralTermsManager, get_viral_terms, add_viral_term, update_viral_term, remove_viral_term
from .viral_vector import ViralVector, get_viral_vector, rebuild_viral_vector
from .similarity import (
    cosine, 
    window_captions, 
    score_windows_against_viral_vector, 
    filter_windows_by_score,
    create_highlight_segments_from_windows
)
from .persist import (
    init_db, 
    upsert_viral_terms, 
    get_viral_terms_from_db, 
    upsert_viral_vector, 
    get_viral_vector_from_db,
    upsert_video_embeddings,
    upsert_viral_scores,
    get_viral_scores,
    get_database_stats
)

__all__ = [
    # Embeddings
    "embed_texts",
    "EmbeddingCache",
    
    # Viral Terms
    "ViralTerm",
    "ViralTermsManager", 
    "get_viral_terms",
    "add_viral_term",
    "update_viral_term",
    "remove_viral_term",
    
    # Viral Vector
    "ViralVector",
    "get_viral_vector",
    "rebuild_viral_vector",
    
    # Similarity
    "cosine",
    "window_captions",
    "score_windows_against_viral_vector",
    "filter_windows_by_score",
    "create_highlight_segments_from_windows",
    
    # Persistence
    "init_db",
    "upsert_viral_terms",
    "get_viral_terms_from_db",
    "upsert_viral_vector",
    "get_viral_vector_from_db",
    "upsert_video_embeddings",
    "upsert_viral_scores",
    "get_viral_scores",
    "get_database_stats"
]
