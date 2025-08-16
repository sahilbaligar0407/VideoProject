"""
Output package for ClipGenius Pipeline v2.
Handles manifest generation and output metadata.
"""

from .manifest import (
    generate_clip_manifest,
    generate_batch_manifest
)

__all__ = [
    "generate_clip_manifest",
    "generate_batch_manifest"
]
