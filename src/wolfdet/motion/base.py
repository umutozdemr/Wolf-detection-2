"""Abstract base interface for motion-trigger providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MotionTrigger(ABC):
    """Stage-1 low-power motion gate that wakes the AI detector."""

    @abstractmethod
    def check_motion(self, frame: Any = None) -> bool:
        """Return True if motion is currently detected."""

    def close(self) -> None:
        """Release any GPIO or OS resources."""
