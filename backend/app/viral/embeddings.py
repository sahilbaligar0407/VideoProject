"""
Text embedding utilities using OpenAI API with caching and normalization.
"""

import hashlib
import json
import os
import pickle
from typing import List, Union
import numpy as np
import openai
from openai import OpenAI
import asyncio
import time

from ..config import settings


class EmbeddingCache:
    """Simple disk cache for embeddings."""
    
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate SHA1 hash for cache key."""
        content = f"{text}:{model}"
        return hashlib.sha1(content.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        """Get full path for cache file."""
        return os.path.join(self.cache_dir, f"{cache_key}.pkl")
    
    def get(self, text: str, model: str) -> Union[np.ndarray, None]:
        """Retrieve embedding from cache if exists."""
        cache_key = self._get_cache_key(text, model)
        cache_path = self._get_cache_path(cache_key)
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"⚠️ Cache read error: {e}")
                return None
        return None
    
    def set(self, text: str, model: str, embedding: np.ndarray):
        """Store embedding in cache."""
        cache_key = self._get_cache_key(text, model)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(embedding, f)
        except Exception as e:
            print(f"⚠️ Cache write error: {e}")


# Global cache instance
_embedding_cache = EmbeddingCache(settings.embed_cache_dir)


async def embed_texts(texts: List[str], batch_size: int = 64) -> List[np.ndarray]:
    """
    Embed a list of texts using OpenAI API with batching and caching.
    
    Args:
        texts: List of text strings to embed
        batch_size: Number of texts to process in each API call
        
    Returns:
        List of normalized embedding vectors (numpy arrays)
    """
    if not texts:
        return []
    
    # Check cache first
    cached_embeddings = []
    texts_to_embed = []
    text_indices = []
    
    for i, text in enumerate(texts):
        cached = _embedding_cache.get(text, settings.embedding_model)
        if cached is not None:
            cached_embeddings.append((i, cached))
        else:
            texts_to_embed.append(text)
            text_indices.append(i)
    
    # If all texts were cached, return in original order
    if not texts_to_embed:
        result = [None] * len(texts)
        for idx, embedding in cached_embeddings:
            result[idx] = embedding
        return result
    
    # Process uncached texts in batches
    new_embeddings = []
    for i in range(0, len(texts_to_embed), batch_size):
        batch = texts_to_embed[i:i + batch_size]
        batch_embeddings = await _embed_batch_with_retry(batch)
        new_embeddings.extend(batch_embeddings)
    
    # Cache new embeddings
    for text, embedding in zip(texts_to_embed, new_embeddings):
        _embedding_cache.set(text, settings.embedding_model, embedding)
    
    # Combine cached and new embeddings in correct order
    result = [None] * len(texts)
    
    # Place cached embeddings
    for idx, embedding in cached_embeddings:
        result[idx] = embedding
    
    # Place new embeddings
    for i, (text_idx, embedding) in enumerate(zip(text_indices, new_embeddings)):
        result[text_idx] = embedding
    
    return result


async def _embed_batch_with_retry(texts: List[str], max_retries: int = 3) -> List[np.ndarray]:
    """
    Embed a batch of texts with exponential backoff retry logic.
    
    Args:
        texts: List of texts to embed
        max_retries: Maximum number of retry attempts
        
    Returns:
        List of normalized embedding vectors
    """
    client = OpenAI(api_key=settings.openai_api_key)
    
    for attempt in range(max_retries):
        try:
            # Clean and prepare texts
            cleaned_texts = [_clean_text_for_embedding(text) for text in texts]
            
            # Make API call
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.embeddings.create(
                    input=cleaned_texts,
                    model=settings.embedding_model
                )
            )
            
            # Extract embeddings and normalize
            embeddings = []
            for embedding_data in response.data:
                vector = np.array(embedding_data.embedding, dtype=np.float32)
                # Normalize to unit vector
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm
                embeddings.append(vector)
            
            return embeddings
            
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                # Rate limit - exponential backoff
                wait_time = (2 ** attempt) * 1.0  # 1s, 2s, 4s
                print(f"⚠️ Rate limited, waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
                continue
            else:
                print(f"❌ Embedding failed after {attempt + 1} attempts: {e}")
                raise
    
    raise Exception("Failed to embed texts after all retry attempts")


def _clean_text_for_embedding(text: str) -> str:
    """
    Clean text for embedding by removing extra whitespace and limiting length.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text suitable for embedding
    """
    # Remove extra whitespace and newlines
    cleaned = " ".join(text.split())
    
    # Limit to reasonable length for embedding (avoid token limits)
    if len(cleaned) > 300:
        cleaned = cleaned[:300] + "..."
    
    return cleaned


def get_embedding_dimension() -> int:
    """Get the dimension of embeddings for the current model."""
    # OpenAI text-embedding-3-small is 1536 dimensions
    if "text-embedding-3-small" in settings.embedding_model:
        return 1536
    elif "text-embedding-3-large" in settings.embedding_model:
        return 3072
    elif "text-embedding-ada-002" in settings.embedding_model:
        return 1536
    else:
        # Default fallback
        return 1536
