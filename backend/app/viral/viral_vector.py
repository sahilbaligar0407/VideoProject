"""
Viral vector computation using weighted centroid of viral terms.
"""

import numpy as np
from typing import Optional, Tuple
from datetime import datetime

from .embeddings import embed_texts
from .viral_terms import get_viral_terms
from .persist import upsert_viral_vector, get_viral_vector_from_db
from ..settings import settings


class ViralVector:
    """Manages the viral vector computation and caching."""
    
    def __init__(self):
        self._cached_vector: Optional[np.ndarray] = None
        self._cached_updated_at: Optional[str] = None
        self._cached_terms_hash: Optional[str] = None
    
    def _compute_terms_hash(self) -> str:
        """Compute hash of current terms for cache invalidation."""
        terms = get_viral_terms()
        terms_str = "|".join([f"{t.term}:{t.weight}" for t in sorted(terms, key=lambda x: x.term)])
        return str(hash(terms_str))
    
    async def get_viral_vector(self) -> Tuple[np.ndarray, str]:
        """
        Get the viral vector, computing it if necessary.
        
        Returns:
            Tuple of (vector, updated_at timestamp)
        """
        # Check if we need to invalidate cache
        current_terms_hash = self._compute_terms_hash()
        
        if (self._cached_vector is not None and 
            self._cached_terms_hash == current_terms_hash):
            return self._cached_vector, self._cached_updated_at
        
        # Try to load from database first
        db_vector, db_updated_at = get_viral_vector_from_db(settings.embedding_model)
        
        if db_vector is not None and db_updated_at is not None:
            # Check if database vector is still valid
            if self._cached_terms_hash == current_terms_hash:
                self._cached_vector = db_vector
                self._cached_updated_at = db_updated_at
                self._cached_terms_hash = current_terms_hash
                return db_vector, db_updated_at
        
        # Need to recompute
        vector, updated_at = await self._compute_viral_vector()
        
        # Cache the result
        self._cached_vector = vector
        self._cached_updated_at = updated_at
        self._cached_terms_hash = current_terms_hash
        
        return vector, updated_at
    
    async def _compute_viral_vector(self) -> Tuple[np.ndarray, str]:
        """
        Compute the viral vector from current terms.
        
        Returns:
            Tuple of (normalized vector, timestamp)
        """
        terms = get_viral_terms()
        
        if not terms:
            # Return zero vector if no terms
            dimension = 1536  # Default for text-embedding-3-small
            zero_vector = np.zeros(dimension, dtype=np.float32)
            timestamp = datetime.now().isoformat()
            return zero_vector, timestamp
        
        # Extract terms and weights
        term_texts = [term.term for term in terms]
        weights = [term.weight for term in terms]
        
        print(f"🤖 Computing viral vector from {len(terms)} terms...")
        
        # Get embeddings for all terms
        embeddings = await embed_texts(term_texts)
        
        if not embeddings or len(embeddings) != len(terms):
            raise Exception("Failed to get embeddings for viral terms")
        
        # Compute weighted centroid
        total_weight = sum(weights)
        weighted_sum = np.zeros_like(embeddings[0], dtype=np.float32)
        
        for embedding, weight in zip(embeddings, weights):
            weighted_sum += weight * embedding
        
        # Normalize by total weight and then to unit vector
        if total_weight > 0:
            centroid = weighted_sum / total_weight
        else:
            centroid = weighted_sum
        
        # Ensure unit vector
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm
        
        # Store in database
        timestamp = datetime.now().isoformat()
        upsert_viral_vector(settings.embedding_model, centroid, timestamp)
        
        print(f"✅ Viral vector computed: {centroid.shape}, norm: {np.linalg.norm(centroid):.6f}")
        
        return centroid, timestamp
    
    def invalidate_cache(self):
        """Invalidate the cached viral vector."""
        self._cached_vector = None
        self._cached_updated_at = None
        self._cached_terms_hash = None


# Global instance
_viral_vector = ViralVector()


async def get_viral_vector() -> Tuple[np.ndarray, str]:
    """
    Get the current viral vector.
    
    Returns:
        Tuple of (vector, updated_at timestamp)
    """
    return await _viral_vector.get_viral_vector()


async def rebuild_viral_vector() -> dict:
    """
    Force rebuild of the viral vector.
    
    Returns:
        Dictionary with vector info
    """
    # Invalidate cache
    _viral_vector.invalidate_cache()
    
    # Recompute
    vector, updated_at = await _viral_vector._compute_viral_vector()
    
    return {
        "vector_size": len(vector),
        "updated_at": updated_at,
        "model": settings.embedding_model,
        "terms_count": len(get_viral_terms())
    }


def invalidate_viral_vector_cache():
    """Invalidate the viral vector cache (called when terms change)."""
    _viral_vector.invalidate_cache()
