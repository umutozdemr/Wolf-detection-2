"""Abstract base interface for wildlife/wolf object detectors."""

from __future__ import annotations

from abc import ABC, abstractmethod

from wolfdet.types import Detection, FramePacket


class WolfDetector(ABC):
    """Common interface for YOLO, ONNX/NCNN, and mock detector implementations."""

    @abstractmethod
    def detect(self, packet: FramePacket) -> list[Detection]:
        """Run object detection on a FramePacket and return normalized Detections."""
