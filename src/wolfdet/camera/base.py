"""Abstract base interface for camera frame sources."""

from __future__ import annotations

from abc import ABC, abstractmethod

from wolfdet.types import FramePacket


class CameraSource(ABC):
    """Unified camera interface across Raspberry Pi Camera Module 3 and PC sources."""

    @abstractmethod
    def open(self) -> None:
        """Initialize camera stream or video file."""

    @abstractmethod
    def read(self) -> FramePacket | None:
        """Capture and return the next FramePacket, or None on end-of-stream."""

    @abstractmethod
    def close(self) -> None:
        """Release camera resources to minimize power draw."""
