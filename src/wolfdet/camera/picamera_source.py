"""Raspberry Pi Camera Module 3 (IMX708) capture backend using picamera2."""

from __future__ import annotations

import time

from wolfdet.camera.base import CameraSource
from wolfdet.types import FramePacket


class PiCameraModule3Source(CameraSource):
    """Low-FPS, HDR-capable capture wrapper for Raspberry Pi Camera Module 3.

    Key hardware features leveraged on Camera Module 3 (IMX708):
      - Phase-Detection Autofocus (PDAF) via libcamera AfMode Continuous
      - Native HDR support for high-contrast forest sunlight/shadow scenes
      - Configurable low FPS (2-5 FPS) to minimize Pi 4B CPU and CSI power draw
    """

    def __init__(
        self,
        width: int = 640,
        height: int = 480,
        fps: float = 4.0,
        autofocus: bool = True,
        hdr: bool = True,
    ) -> None:
        self.width = width
        self.height = height
        self.fps = max(1.0, fps)
        self.autofocus = autofocus
        self.hdr = hdr
        self._picam = None
        self._frame_id = 0

    def open(self) -> None:
        try:
            from libcamera import controls  # type: ignore
            from picamera2 import Picamera2  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "picamera2 / libcamera not available. Run on Raspberry Pi OS with "
                "'sudo apt install python3-picamera2' or select camera.backend='opencv'."
            ) from exc

        self._picam = Picamera2()
        frame_duration_us = int(1_000_000 / self.fps)
        config = self._picam.create_video_configuration(
            main={"size": (self.width, self.height), "format": "RGB888"},
            controls={"FrameDurationLimits": (frame_duration_us, frame_duration_us)},
        )
        self._picam.configure(config)

        if self.autofocus and hasattr(controls, "AfModeEnum"):
            self._picam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        if self.hdr and hasattr(controls, "HdrModeEnum"):
            self._picam.set_controls({"HdrMode": controls.HdrModeEnum.SingleExposure})

        self._picam.start()
        # Brief warm-up for auto-exposure / autofocus settle
        time.sleep(0.3)

    def read(self) -> FramePacket | None:
        if self._picam is None:
            return None
        frame = self._picam.capture_array()
        self._frame_id += 1
        return FramePacket(
            frame_id=self._frame_id,
            timestamp=time.monotonic(),
            image=frame,
            scenario_tag="picamera3_live",
        )

    def close(self) -> None:
        if self._picam is not None:
            self._picam.stop()
            self._picam.close()
            self._picam = None
