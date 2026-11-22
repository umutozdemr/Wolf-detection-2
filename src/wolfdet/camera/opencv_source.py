"""OpenCV video/webcam camera source and built-in Midterm 3-scenario demo source."""

from __future__ import annotations

from dataclasses import dataclass
import time

from wolfdet.camera.base import CameraSource
from wolfdet.types import FramePacket


class OpenCVCameraSource(CameraSource):
    """Captures frames from a PC webcam (index '0') or wildlife camera-trap video file."""

    def __init__(self, source: str = "0", width: int = 640, height: int = 480) -> None:
        self.source = source
        self.width = width
        self.height = height
        self._cap = None
        self._frame_id = 0

    def open(self) -> None:
        try:
            import cv2  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "opencv-python is required for OpenCVCameraSource. "
                "Install requirements.txt or run with --demo-scenarios."
            ) from exc

        src: int | str = int(self.source) if self.source.isdigit() else self.source
        self._cap = cv2.VideoCapture(src)
        if not self._cap.isOpened():
            raise RuntimeError(f"Could not open video/camera source: {self.source}")
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def read(self) -> FramePacket | None:
        if self._cap is None:
            return None
        ok, frame = self._cap.read()
        if not ok:
            return None
        self._frame_id += 1
        return FramePacket(
            frame_id=self._frame_id,
            timestamp=time.monotonic(),
            image=frame,
            scenario_tag=f"source:{self.source}",
        )

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None


@dataclass(frozen=True)
class ScenarioSegment:
    """Single scripted wildlife/field segment for deterministic Midterm demos."""

    name: str
    frames: int
    motion: bool
    simulated_time_step_s: float = 1.0


class SyntheticScenarioCamera(CameraSource):
    """Generates the 3 core Midterm presentation scenarios without requiring video files:

    1. Quiet forest (IDLE standby) -> Deer passes (Non-target ignored -> returns to IDLE)
    2. Human hiker passes -> GDPR Privacy Guard wipes buffer & suppresses playback
    3. Wolf arrives -> 3-of-5 temporal confirmation -> Human speech deterrence -> Cooldown -> IDLE

    If OpenCV + NumPy are installed, renders crisp visual demo frames; otherwise emits
    lightweight headless FramePackets for CLI & automated testing.
    """

    DEFAULT_SEGMENTS: tuple[ScenarioSegment, ...] = (
        ScenarioSegment("quiet_forest_idle", frames=3, motion=False, simulated_time_step_s=1.0),
        ScenarioSegment("deer_non_target", frames=6, motion=True, simulated_time_step_s=3.5),
        ScenarioSegment("quiet_between_1", frames=2, motion=False, simulated_time_step_s=1.0),
        ScenarioSegment("human_hiker_gdpr", frames=5, motion=True, simulated_time_step_s=4.0),
        ScenarioSegment("quiet_between_2", frames=2, motion=False, simulated_time_step_s=1.0),
        ScenarioSegment("wolf_confirmed", frames=6, motion=True, simulated_time_step_s=1.0),
        ScenarioSegment("post_wolf_cooldown", frames=4, motion=False, simulated_time_step_s=10.0),
    )

    def __init__(
        self,
        segments: tuple[ScenarioSegment, ...] | None = None,
        width: int = 640,
        height: int = 480,
        render_images: bool = True,
    ) -> None:
        self.segments = segments or self.DEFAULT_SEGMENTS
        self.width = width
        self.height = height
        self.render_images = render_images
        self._timeline: list[tuple[str, bool, float]] = []
        self._cursor = 0
        self._sim_time = 0.0
        self._frame_id = 0

    def open(self) -> None:
        self._timeline = []
        for seg in self.segments:
            for _ in range(seg.frames):
                self._timeline.append((seg.name, seg.motion, seg.simulated_time_step_s))
        self._cursor = 0
        self._sim_time = 100.0
        self._frame_id = 0

    def read(self) -> FramePacket | None:
        if self._cursor >= len(self._timeline):
            return None
        tag, motion, dt = self._timeline[self._cursor]
        self._cursor += 1
        self._frame_id += 1
        self._sim_time += dt

        image = self._render_synthetic_frame(tag) if self.render_images else None
        return FramePacket(
            frame_id=self._frame_id,
            timestamp=self._sim_time,
            image=image,
            scenario_tag=tag,
            motion_detected=motion,
        )

    def _render_synthetic_frame(self, tag: str):
        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore
        except ImportError:
            return None

        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        # Forest twilight background gradient
        canvas[:, :] = (34, 48, 32)
        cv2.rectangle(canvas, (0, int(self.height * 0.68)), (self.width, self.height), (28, 40, 26), -1)

        # Stylized pine silhouettes
        for x in (60, 140, 500, 580):
            pts = np.array([[x, 120], [x - 35, 330], [x + 35, 330]], np.int32)
            cv2.fillPoly(canvas, [pts], (22, 36, 22))

        label_map = {
            "quiet_forest_idle": "SCENARIO: Quiet Forest (No Motion)",
            "deer_non_target": "SCENARIO 1: Roe Deer Passing (Non-Target)",
            "human_hiker_gdpr": "SCENARIO 2: Human Hiker (GDPR Privacy Filter)",
            "wolf_confirmed": "SCENARIO 3: Grey Wolf Approaching (Target!)",
            "post_wolf_cooldown": "POST-PLAYBACK: Wolf Fled -> Cooldown Window",
        }
        title = label_map.get(tag, f"SCENARIO: {tag}")
        cv2.putText(canvas, title, (18, self.height - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (220, 235, 220), 2)
        return canvas

    def close(self) -> None:
        self._timeline = []
