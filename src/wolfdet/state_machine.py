"""Energy-aware finite-state machine for wolf detection and deterrence.

Transitions:
    IDLE --(motion trigger)--> DETECTING
    DETECTING --(wolf confirmed M-of-N frames)--> RESPONDING
    DETECTING --(detect window expires / non-target)--> IDLE
    DETECTING --(person detected: GDPR guard)--> suppress recording & ignore deterrence
    RESPONDING --(delay + human speech playback + log)--> COOLDOWN
    COOLDOWN --(cooldown elapsed)--> IDLE
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
import time
import uuid

from wolfdet.audio.deterrent import AudioDeterrent
from wolfdet.config import AppConfig
from wolfdet.detection.base import WolfDetector
from wolfdet.power.energy_model import RuntimeEnergyTracker
from wolfdet.recorder.event_logger import EventRecorder
from wolfdet.types import Detection, EventRecord, FramePacket, StepResult, SystemState


class WolfResponseStateMachine:
    """Coordinates motion gating, AI confirmation, GDPR filtering, and ABR playback."""

    def __init__(
        self,
        config: AppConfig,
        detector: WolfDetector,
        audio: AudioDeterrent,
        recorder: EventRecorder,
        energy_tracker: RuntimeEnergyTracker | None = None,
    ) -> None:
        self.config = config
        self.detector = detector
        self.audio = audio
        self.recorder = recorder
        self.energy = energy_tracker or RuntimeEnergyTracker(config.power_model)

        self.state: SystemState = SystemState.IDLE
        self._detect_started_at: float = 0.0
        self._motion_triggered_at: float = 0.0
        self._cooldown_until: float = 0.0
        self._last_tick_at: float | None = None

        self._wolf_window: deque[bool] = deque(maxlen=max(1, config.detection.confirm_window))
        self._best_wolf_conf: float = 0.0
        self._privacy_logged_in_window: bool = False
        self._non_target_seen: str | None = None

        self.events: list[EventRecord] = []

    def reset_window(self) -> None:
        self._wolf_window.clear()
        self._best_wolf_conf = 0.0
        self._privacy_logged_in_window = False
        self._non_target_seen = None

    def step(self, packet: FramePacket, motion_active: bool) -> StepResult:
        """Advance the state machine by one frame/tick."""
        now = packet.timestamp
        prev_state = self.state
        dt = 0.25 if self._last_tick_at is None else max(0.0, now - self._last_tick_at)
        self._last_tick_at = now

        # Always track power consumption for the state we spent the last interval in.
        est_power = self.energy.record_interval(self.state, dt)

        # 1. COOLDOWN state: wait until cooldown timer expires
        if self.state == SystemState.COOLDOWN:
            if now >= self._cooldown_until:
                self.state = SystemState.IDLE
                self.reset_window()
                return StepResult(
                    state=self.state,
                    previous_state=prev_state,
                    frame_id=packet.frame_id,
                    estimated_power_w=self.energy.power_for_state(self.state),
                    status_message="Cooldown finished; returning to low-power IDLE.",
                )
            remaining = max(0.0, self._cooldown_until - now)
            return StepResult(
                state=self.state,
                previous_state=prev_state,
                frame_id=packet.frame_id,
                estimated_power_w=est_power,
                status_message=f"Cooldown active ({remaining:.1f}s remaining); AI & amp off.",
            )

        # 2. IDLE state: stay in low power until motion triggers wake-up
        if self.state == SystemState.IDLE:
            if motion_active or packet.motion_detected:
                self.state = SystemState.DETECTING
                self._detect_started_at = now
                self._motion_triggered_at = now
                self.reset_window()
                self.recorder.clear_buffer()
                return StepResult(
                    state=self.state,
                    previous_state=prev_state,
                    frame_id=packet.frame_id,
                    estimated_power_w=self.energy.power_for_state(self.state),
                    status_message="Motion trigger received -> waking camera & AI detector.",
                )
            return StepResult(
                state=self.state,
                previous_state=prev_state,
                frame_id=packet.frame_id,
                estimated_power_w=est_power,
                status_message="IDLE (low-power standby; awaiting PIR/motion trigger).",
            )

        # 3. DETECTING state: run AI detector on frame
        t0 = time.perf_counter()
        raw_detections = self.detector.detect(packet)
        inference_ms = (time.perf_counter() - t0) * 1000.0

        filtered = self._filter_detections(raw_detections)

        # 3a. GDPR / Privacy Guard: drop frame immediately if a human is present
        if self._contains_privacy_class(filtered):
            self.recorder.clear_buffer()
            self._wolf_window.append(False)
            privacy_event: EventRecord | None = None
            if not self._privacy_logged_in_window:
                self._privacy_logged_in_window = True
                privacy_event = self._build_event(
                    event_type="PRIVACY_SUPPRESSED",
                    species="person",
                    max_conf=max(
                        (d.confidence for d in filtered if d.label in self.config.detection.privacy_classes),
                        default=0.0,
                    ),
                    audio_exemplar=None,
                    latency_ms=inference_ms,
                    clip_path=None,
                    notes="GDPR guard: human detected; frame buffer wiped, audio suppressed.",
                    detections=[],
                )
                self.recorder.log_event(privacy_event)
                self.events.append(privacy_event)

            return StepResult(
                state=self.state,
                previous_state=prev_state,
                frame_id=packet.frame_id,
                detections=filtered,
                inference_ms=inference_ms,
                estimated_power_w=self.energy.power_for_state(self.state),
                privacy_suppressed=True,
                event_record=privacy_event,
                status_message="GDPR Privacy Guard: person detected -> buffer wiped, no recording/audio.",
            )

        # Safe to push frame into circular pre-trigger ring buffer
        self.recorder.push_frame(packet)

        wolf_detections = [
            d for d in filtered if d.label in self.config.detection.target_classes
        ]
        if wolf_detections:
            self._wolf_window.append(True)
            self._best_wolf_conf = max(
                self._best_wolf_conf, max(d.confidence for d in wolf_detections)
            )
        else:
            self._wolf_window.append(False)
            if filtered:
                self._non_target_seen = filtered[0].label

        hits = sum(self._wolf_window)
        required_hits = self.config.detection.confirm_hits

        # 3b. Temporal Confirmation reached -> RESPONDING
        if hits >= required_hits:
            self.state = SystemState.RESPONDING
            self.energy.record_interval(
                SystemState.RESPONDING,
                self.config.response.pre_playback_delay_s + self.config.response.playback_duration_s,
            )

            end_to_end_ms = max(inference_ms, (now - self._motion_triggered_at) * 1000.0)
            exemplar = self.audio.trigger_deterrent(
                delay_s=self.config.response.pre_playback_delay_s,
                duration_s=self.config.response.playback_duration_s,
            )
            clip_path = self.recorder.save_buffered_clip(
                prefix=f"wolf_{packet.frame_id:05d}"
            )
            event = self._build_event(
                event_type="WOLF_DETERRENCE",
                species="wolf",
                max_conf=self._best_wolf_conf,
                audio_exemplar=exemplar,
                latency_ms=end_to_end_ms,
                clip_path=clip_path,
                notes=(
                    f"Confirmed {hits}/{len(self._wolf_window)} frames. "
                    f"Played randomized human speech exemplar '{exemplar}'."
                ),
                detections=[d.to_dict() for d in wolf_detections],
            )
            self.recorder.log_event(event)
            self.events.append(event)

            # Transition directly into COOLDOWN after synchronous playback trigger
            self.state = SystemState.COOLDOWN
            self._cooldown_until = now + self.config.response.cooldown_s
            self.reset_window()

            return StepResult(
                state=SystemState.RESPONDING,
                previous_state=prev_state,
                frame_id=packet.frame_id,
                detections=filtered,
                inference_ms=inference_ms,
                estimated_power_w=self.energy.power_for_state(SystemState.RESPONDING),
                deterrent_triggered=True,
                audio_exemplar=exemplar,
                event_record=event,
                status_message=(
                    f"WOLF CONFIRMED ({hits}/{self.config.detection.confirm_window}) -> "
                    f"Human speech '{exemplar}' triggered!"
                ),
            )

        # 3c. Detection window timeout -> return to IDLE (saves energy!)
        if (now - self._detect_started_at) >= self.config.motion.detect_window_s:
            ignored_event: EventRecord | None = None
            if self._non_target_seen:
                ignored_event = self._build_event(
                    event_type="NON_TARGET_IGNORED",
                    species=self._non_target_seen,
                    max_conf=0.0,
                    audio_exemplar=None,
                    latency_ms=inference_ms,
                    clip_path=None,
                    notes=(
                        f"Non-target wildlife/scene ('{self._non_target_seen}') ignored; "
                        "no playback triggered."
                    ),
                    detections=[],
                )
                self.recorder.log_event(ignored_event)
                self.events.append(ignored_event)

            self.state = SystemState.IDLE
            self.reset_window()
            self.recorder.clear_buffer()
            return StepResult(
                state=self.state,
                previous_state=prev_state,
                frame_id=packet.frame_id,
                detections=filtered,
                inference_ms=inference_ms,
                estimated_power_w=self.energy.power_for_state(self.state),
                event_record=ignored_event,
                status_message="Detection window expired (no wolf) -> returning to IDLE.",
            )

        # Still inside DETECTING window
        labels_str = ", ".join(f"{d.label}({d.confidence:.2f})" for d in filtered) or "none"
        return StepResult(
            state=self.state,
            previous_state=prev_state,
            frame_id=packet.frame_id,
            detections=filtered,
            inference_ms=inference_ms,
            estimated_power_w=self.energy.power_for_state(self.state),
            status_message=(
                f"DETECTING [{labels_str}] | wolf votes: {hits}/{required_hits}"
            ),
        )

    def _filter_detections(self, detections: list[Detection]) -> list[Detection]:
        out: list[Detection] = []
        for det in detections:
            label = det.label.lower().strip()
            if self.config.detection.demo_dog_as_wolf_proxy and label == "dog":
                label = "wolf"
            if det.confidence >= self.config.detection.conf_threshold:
                out.append(Detection(label=label, confidence=det.confidence, bbox=det.bbox))
        return out

    def _contains_privacy_class(self, detections: list[Detection]) -> bool:
        privacy_set = {c.lower() for c in self.config.detection.privacy_classes}
        return any(d.label in privacy_set for d in detections)

    def _build_event(
        self,
        event_type: str,
        species: str,
        max_conf: float,
        audio_exemplar: str | None,
        latency_ms: float,
        clip_path: str | None,
        notes: str,
        detections: list[dict],
    ) -> EventRecord:
        return EventRecord(
            event_id=uuid.uuid4().hex[:10],
            device_id=self.config.system.device_id,
            timestamp_iso=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            event_type=event_type,
            species=species,
            max_confidence=max_conf,
            confirm_hits=sum(self._wolf_window),
            confirm_window=self.config.detection.confirm_window,
            audio_exemplar=audio_exemplar,
            pre_playback_delay_s=self.config.response.pre_playback_delay_s,
            playback_duration_s=self.config.response.playback_duration_s,
            end_to_end_latency_ms=latency_ms,
            clip_path=clip_path,
            notes=notes,
            detections=detections,
        )
