"""Circular pre-trigger frame buffer, clip writer, and JSONL/CSV event logger."""

from __future__ import annotations

from collections import deque
import csv
import json
from pathlib import Path

from wolfdet.types import EventRecord, FramePacket


class EventRecorder:
    """Retains a pre-trigger ring buffer and logs structured ABR telemetry events.

    GDPR Privacy Guarantee:
        When a person is detected, `clear_buffer()` immediately wipes all RAM-buffered
        frames so no image of a passing human is ever persisted to disk.
    """

    CSV_FIELDS: tuple[str, ...] = (
        "event_id",
        "device_id",
        "timestamp_iso",
        "event_type",
        "species",
        "max_confidence",
        "confirm_hits",
        "confirm_window",
        "audio_exemplar",
        "pre_playback_delay_s",
        "playback_duration_s",
        "end_to_end_latency_ms",
        "clip_path",
        "notes",
    )

    def __init__(
        self,
        log_dir: str | Path = "logs",
        recording_dir: str | Path = "recordings",
        max_buffer_frames: int = 16,
        fps: float = 4.0,
        save_video_clips: bool = True,
        enabled: bool = True,
    ) -> None:
        self.log_dir = Path(log_dir)
        self.recording_dir = Path(recording_dir)
        self.fps = max(1.0, fps)
        self.save_video_clips = save_video_clips
        self.enabled = enabled
        self._buffer: deque[FramePacket] = deque(maxlen=max(1, max_buffer_frames))

        if self.enabled:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.recording_dir.mkdir(parents=True, exist_ok=True)

        self.jsonl_path = self.log_dir / "events.jsonl"
        self.csv_path = self.log_dir / "events.csv"

    def push_frame(self, packet: FramePacket) -> None:
        if self.enabled:
            self._buffer.append(packet)

    def clear_buffer(self) -> None:
        """Immediately wipe all frames held in RAM (e.g. on GDPR person detection)."""
        self._buffer.clear()

    @property
    def buffered_frame_count(self) -> int:
        return len(self._buffer)

    def save_buffered_clip(self, prefix: str = "wolf_event") -> str | None:
        """Persist buffered frames as an MP4 clip (when OpenCV images exist)."""
        if not (self.enabled and self.save_video_clips):
            return None

        frames = [pkt.image for pkt in self._buffer if pkt.image is not None]
        if not frames:
            return None

        try:
            import cv2  # type: ignore
        except ImportError:
            return None

        self.recording_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.recording_dir / f"{prefix}.mp4"
        height, width = frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_path), fourcc, self.fps, (width, height))
        try:
            for img in frames:
                writer.write(img)
        finally:
            writer.release()

        return str(out_path)

    def log_event(self, event: EventRecord) -> None:
        """Append event to both JSONL (rich schema) and CSV (spreadsheet/SPSS ready)."""
        if not self.enabled:
            return

        self.log_dir.mkdir(parents=True, exist_ok=True)
        payload = event.to_dict()

        with self.jsonl_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

        write_header = not self.csv_path.exists()
        with self.csv_path.open("a", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=self.CSV_FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerow({k: payload.get(k, "") for k in self.CSV_FIELDS})
