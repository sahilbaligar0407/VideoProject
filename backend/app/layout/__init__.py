"""
Layout package for ClipGenius Pipeline v2.
Handles dynamic layout switching, state machines, and face-aware rendering.
"""

from .state_machine import (
    LayoutStateMachine,
    LayoutState,
    FaceTrack,
    StateTransition
)

__all__ = [
    "LayoutStateMachine",
    "LayoutState", 
    "FaceTrack",
    "StateTransition"
]
