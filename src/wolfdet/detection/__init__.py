"""Object detection backends (YOLO/ONNX/NCNN and deterministic scenario mock)."""

from wolfdet.detection.base import WolfDetector
from wolfdet.detection.mock_detector import ScenarioMockDetector
from wolfdet.detection.yolo_detector import YOLOWolfDetector

__all__ = ["WolfDetector", "YOLOWolfDetector", "ScenarioMockDetector"]
