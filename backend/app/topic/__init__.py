"""
Topic-driven clip search for ClipGenius.
"""

from .search import (
    keyword_spans,
    embedding_spans,
    topic_windows,
    topic_windows_embedding
)

__all__ = [
    "keyword_spans",
    "embedding_spans",
    "topic_windows",
    "topic_windows_embedding"
]
