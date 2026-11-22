"""Core data structures shared across all WolfDet modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SystemState(str, Enum):
    """Finite-state machine modes of the energy-aware wolf response node."""

    IDLE = "IDLE"
    DETECTING = "DETECTING"
    RESPONDING = "RESPONDING"
    COOLDOWN = "COOLDOWN"


@dataclass(frozen=True)
class BoundingBox:
    """Axis-aligned pixel bounding box (x1, y1, x2, y2)."""

    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        return max(0, self.x2 - self.x1)

    @property
    def height(self) -> int:
        return max(0, self.y2 - self.y1)

    def to_dict(self) -> dict[str, int]:
        return {"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2}


@dataclass(frozen=True)
class Detection:
    """Single object detection output from any detector backend."""

    label: str
    confidence: float
    bbox: BoundingBox

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 4),
            "bbox": self.bbox.to_dict(),
        }


@dataclass
class FramePacket:
    """Captured frame plus metadata traveling through the processing pipeline."""

    frame_id: int
    timestamp: float
    image: Any = None  # numpy.ndarray when OpenCV/picamera2 is active; optional in headless tests
    scenario_tag: str = ""
    motion_detected: bool = False


@dataclass
class EventRecord:
    """Structured event emitted for ABR behavioral & system evaluation."""

    event_id: str
    device_id: str
    timestamp_iso: str
    event_type: str  # "WOLF_DETERRENCE" | "NON_TARGET_IGNORED" | "PRIVACY_SUPPRESSED"
    species: str
    max_confidence: float
    confirm_hits: int
    confirm_window: int
    audio_exemplar: str | None
    pre_playback_delay_s: float
    playback_duration_s: float
    end_to_end_latency_ms: float
    clip_path: str | None = None
    notes: str = ""
    detections: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "device_id": self.device_id,
            "timestamp_iso": self.timestamp_iso,
            "event_type": self.event_type,
            "species": self.species,
            "max_confidence": round(self.max_confidence, 4),
            "confirm_hits": self.confirm_hits,
            "confirm_window": self.confirm_window,
            "audio_exemplar": self.audio_exemplar,
            "pre_playback_delay_s": self.pre_playback_delay_s,
            "playback_duration_s": self.playback_duration_s,
            "end_to_end_latency_ms": round(self.end_to_end_latency_ms, 2),
            "clip_path": self.clip_path,
            "notes": self.notes,
            "detections": self.detections,
        }


@dataclass
class StepResult:
    """Result returned on each tick of the WolfResponseStateMachine."""

    state: SystemState
    previous_state: SystemState
    frame_id: int
    detections: list[Detection] = field(default_factory=list)
    inference_ms: float = 0.0
    estimated_power_w: float = 0.0
    privacy_suppressed: bool = False
    deterrent_triggered: bool = False
    audio_exemplar: str | None = None
    event_record: EventRecord | None = None
    status_message: str = ""
