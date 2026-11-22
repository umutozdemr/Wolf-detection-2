"""Software frame-differencing motion trigger and deterministic mock trigger."""

from __future__ import annotations

from typing import Any, Iterable

from wolfdet.motion.base import MotionTrigger


class SoftwareMotionTrigger(MotionTrigger):
    """Lightweight grayscale frame-differencing gate for PC/video testing.

    Acts as a drop-in stand-in for the HC-SR501 PIR sensor before hardware
    assembly is completed, keeping the exact same state-machine interface.
    """

    def __init__(
        self,
        diff_threshold: int = 25,
        min_area_ratio: float = 0.01,
    ) -> None:
        self.diff_threshold = diff_threshold
        self.min_area_ratio = min_area_ratio
        self._prev_gray: Any = None

    def check_motion(self, frame: Any = None) -> bool:
        if frame is None:
            return False
        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore
        except ImportError:
            # Without OpenCV/NumPy (pure stdlib demo mode), delegate to frame metadata.
            return True

        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        gray = cv2.GaussianBlur(gray, (15, 15), 0)

        if self._prev_gray is None or self._prev_gray.shape != gray.shape:
            self._prev_gray = gray
            return True

        delta = cv2.absdiff(self._prev_gray, gray)
        self._prev_gray = gray
        _, thresh = cv2.threshold(delta, self.diff_threshold, 255, cv2.THRESH_BINARY)
        changed_ratio = float(np.count_nonzero(thresh)) / float(thresh.size)
        return changed_ratio >= self.min_area_ratio


class MockMotionTrigger(MotionTrigger):
    """Deterministic motion sequence for automated tests and scripted demos."""

    def __init__(self, pattern: Iterable[bool] | None = None, default: bool = False) -> None:
        self._pattern = iter(pattern) if pattern is not None else None
        self._default = default

    def check_motion(self, frame: Any = None) -> bool:
        if self._pattern is None:
            return self._default
        return next(self._pattern, self._default)
