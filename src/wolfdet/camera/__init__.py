"""Camera capture backends (Raspberry Pi Camera Module 3, OpenCV, Synthetic Demo)."""

from wolfdet.camera.base import CameraSource
from wolfdet.camera.opencv_source import OpenCVCameraSource, SyntheticScenarioCamera
from wolfdet.camera.picamera_source import PiCameraModule3Source

__all__ = [
    "CameraSource",
    "PiCameraModule3Source",
    "OpenCVCameraSource",
    "SyntheticScenarioCamera",
]
